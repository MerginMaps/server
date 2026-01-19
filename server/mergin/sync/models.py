# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from __future__ import annotations
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Set, Tuple
from dataclasses import dataclass, asdict
import logging

from blinker import signal
from flask_login import current_user
from pygeodiff import GeoDiff
from sqlalchemy import text, null, desc, nullslast, tuple_
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, UUID, JSONB, ENUM
from sqlalchemy.types import String
from sqlalchemy.ext.hybrid import hybrid_property
from pygeodiff.geodifflib import GeoDiffLibError, GeoDiffLibConflictError
from flask import current_app

from .files import (
    DeltaChangeMerged,
    DeltaDiffFile,
    DeltaChange,
    DeltaChangeSchema,
    ProjectDiffFile,
    ProjectFileChange,
    ChangesSchema,
    ProjectFile,
    files_changes_from_upload,
    mergin_secure_filename,
    PushChangeType,
)
from .interfaces import WorkspaceRole
from .storages.disk import move_to_tmp
from ..app import db
from .storages import DiskStorage
from .utils import (
    LOG_BASE,
    Checkpoint,
    generate_checksum,
    Toucher,
    get_chunk_location,
    get_project_path,
    is_supported_type,
    is_versioned_file,
    is_qgis,
)

Storages = {"local": DiskStorage}
project_deleted = signal("project_deleted")
project_access_granted = signal("project_access_granted")
push_finished = signal("push_finished")
project_version_created = signal("project_version_created")


class FileSyncErrorType(Enum):
    CORRUPTED = "corrupted"
    UNSUPPORTED = "unsupported"
    SYNC_ERROR = "sync error"


class ChangeComparisonAction(Enum):
    """Actions to take when comparing two changes"""

    REPLACE = "replace"
    DELETE = "delete"
    UPDATE = "update"
    UPDATE_DIFF = "update_diff"
    EXCLUDE = "exclude"  # Return None to exclude the file


class Project(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, index=True)
    storage_params = db.Column(db.JSON)
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    tags = db.Column(ARRAY(String), server_default="{}")
    # disk_usage & latest_version are cached properties to keep even if versions are deleted
    disk_usage = db.Column(BIGINT, nullable=False, default=0)
    latest_version = db.Column(db.Integer, index=True)
    workspace_id = db.Column(db.Integer, index=True, nullable=False)
    removed_at = db.Column(db.DateTime, index=True)
    removed_by = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True, index=True
    )
    public = db.Column(db.Boolean, default=False, index=True, nullable=False)
    locked_until = db.Column(db.DateTime, index=True)

    creator = db.relationship(
        "User", uselist=False, backref=db.backref("projects"), foreign_keys=[creator_id]
    )

    project_users = db.relationship(
        "ProjectUser", cascade="all, delete-orphan", back_populates="project"
    )

    __table_args__ = (db.UniqueConstraint("name", "workspace_id"),)

    def __init__(
        self, name, storage_params, creator, workspace, **kwargs
    ):  # pylint: disable=W0613
        self.name = name
        self.storage_params = storage_params
        self.workspace_id = workspace.id
        self.creator = creator
        self.latest_version = 0
        self.public = kwargs.get("public", False)
        latest_files = LatestProjectFiles(project=self)
        db.session.add(latest_files)

    @property
    def storage(self):
        if not self.storage_params:
            return
        if not hasattr(self, "_storage"):  # best approach, seriously
            StorageBackend = Storages[self.storage_params["type"]]
            self._storage = StorageBackend(self)  # pylint: disable=W0201
        return self._storage

    @hybrid_property
    def workspace(self):
        """Discover project workspace"""
        project_workspace = current_app.ws_handler.get(self.workspace_id)
        return project_workspace

    def cache_latest_files(self) -> None:
        """Get project files from changes (FileHistory) and save them for later use."""
        if self.latest_version is None:
            return

        query = f"""
            WITH latest_changes AS (
                SELECT
                    fp.id,
                    pv.project_id,
                    max(pv.name) AS version
                FROM
                    project_version pv
                    LEFT OUTER JOIN file_history fh ON fh.version_id = pv.id
                    LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
                WHERE
                    pv.project_id = :project_id
                    AND pv.name <= :latest_version
                GROUP BY
                    fp.id, pv.project_id
            ), aggregates AS (
                SELECT
                    project_id,
                    COALESCE(array_agg(fh.id) FILTER (WHERE fh.change != 'delete'), ARRAY[]::INTEGER[]) AS files_ids
                FROM latest_changes ch
                LEFT OUTER JOIN file_history fh ON (fh.file_path_id = ch.id AND fh.project_version_name = ch.version)
                GROUP BY project_id
            )
            UPDATE latest_project_files pf
            SET file_history_ids = a.files_ids
            FROM aggregates a
            WHERE a.project_id = pf.project_id;
        """
        params = {"project_id": self.id, "latest_version": self.latest_version}
        db.session.execute(text(query), params)
        db.session.commit()

    @property
    def files(self) -> List[ProjectFile]:
        """Return project files at latest version"""
        # cache file history ids if needed
        if self.latest_project_files.file_history_ids is None:
            self.cache_latest_files()

        if not self.latest_project_files.file_history_ids:
            return []

        query = f"""
            WITH files_ids AS (
                SELECT
                    unnest(file_history_ids) AS fh_id
                FROM latest_project_files
                WHERE project_id = :project_id
            )
            SELECT
                fp.path,
                fh.size,
                fh.location,
                fh.checksum,
                pv.created AS mtime,
                fd.path as diff_path,
                fd.size as diff_size,
                fd.checksum as diff_checksum,
                fd.location as diff_location
            FROM files_ids
            LEFT OUTER JOIN file_history fh ON fh.id = files_ids.fh_id
            LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
            LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
            LEFT OUTER JOIN file_diff fd ON fd.file_path_id = fh.file_path_id AND fd.version = fh.project_version_name and fd.rank = 0;
        """
        params = {"project_id": self.id}
        files = [
            ProjectFile(
                path=row.path,
                size=row.size,
                checksum=row.checksum,
                location=row.location,
                mtime=row.mtime,
                diff=(
                    ProjectDiffFile(
                        path=row.diff_path,
                        size=row.diff_size,
                        checksum=row.diff_checksum,
                        location=row.diff_location,
                    )
                    if row.diff_path
                    else None
                ),
            )
            for row in db.session.execute(text(query), params).fetchall()
        ]
        return files

    def sync_failed(self, client, error_type, error_details, user_id):
        """Commit failed attempt to sync failure history table"""
        new_failure = SyncFailuresHistory(
            self, client, error_type, error_details, user_id
        )
        db.session.add(new_failure)
        db.session.commit()

    def get_latest_version(self):
        """Return ProjectVersion object for the latest project version"""
        return ProjectVersion.query.filter_by(
            project_id=self.id, name=self.latest_version
        ).first()

    def next_version(self):
        """Next project version"""
        return self.latest_version + 1

    @property
    def expiration(self) -> timedelta:
        """Expiration of the project marked for removal
        i.e. if a user deletes a project - in what time it will be removed from database
        It will be possible to create a new project using the same name and will not be possible to restore the old one after this time.
        This time should be used to remove all local copies of the file."""
        initial = timedelta(days=current_app.config["DELETED_PROJECT_EXPIRATION"])
        return initial - (datetime.utcnow() - self.removed_at)

    def delete(self, removed_by: int = None):
        """Mark project as permanently deleted (but keep in db)
        - rename (to free up the same name)
        - remove associated files and their history
        - reset project_access
        - decline pending project access requests
        """
        # do nothing if the project has been already deleted
        if not self.storage_params:
            return
        self.name = f"{self.name}_{str(self.id)}"
        # make sure remove_at is not null as it is used as filter for APIs
        if not self.removed_at:
            self.removed_at = datetime.utcnow()
        if not self.removed_by:
            self.removed_by = removed_by
        # Null in storage params serves as permanent deletion flag
        self.storage.delete()
        self.storage_params = null()
        # remove file records and their history (cascade)
        files_path_table = ProjectFilePath.__table__
        db.session.execute(
            files_path_table.delete().where(files_path_table.c.project_id == self.id)
        )
        # reset project files cache
        files_cache = LatestProjectFiles.query.filter_by(project_id=self.id).first()
        files_cache.file_history_ids = null()
        # remove pending uploads
        upload_table = Upload.__table__
        db.session.execute(
            upload_table.delete().where(upload_table.c.project_id == self.id)
        )
        # remove project version delta related to project
        delta_table = ProjectVersionDelta.__table__
        db.session.execute(
            delta_table.delete().where(delta_table.c.project_id == self.id)
        )
        self.project_users.clear()
        access_requests = (
            AccessRequest.query.filter_by(project_id=self.id)
            .filter(AccessRequest.status.is_(None))
            .all()
        )
        for req in access_requests:
            req.resolve(status=RequestStatus.DECLINED, resolved_by=self.removed_by)
        db.session.commit()
        project_deleted.send(self)

    def _member(self, user_id: int) -> Optional[ProjectUser]:
        """Return association object for user_id"""
        return next((u for u in self.project_users if u.user_id == user_id), None)

    def get_role(self, user_id: int) -> Optional[ProjectRole]:
        """Get user role"""
        member = self._member(user_id)
        if member:
            return ProjectRole(member.role)

    def set_role(self, user_id: int, role: ProjectRole) -> None:
        """Set user role"""
        member = self._member(user_id)
        if member:
            member.role = role.value
        else:
            project_access_granted.send(self, user_id=user_id)
            self.project_users.append(ProjectUser(user_id=user_id, role=role.value))

    def unset_role(self, user_id: int) -> None:
        """Remove user's role"""
        member = self._member(user_id)
        if member:
            self.project_users.remove(member)

    def get_member(self, user_id: int) -> Optional[ProjectMember]:
        """Get project member"""
        from .permissions import ProjectPermissions

        member = self._member(user_id)
        if member:
            return ProjectMember(
                id=user_id,
                username=member.user.username,
                email=member.user.email,
                project_role=ProjectRole(member.role),
                workspace_role=self.workspace.get_user_role(member.user),
                role=ProjectPermissions.get_user_project_role(self, member.user),
            )

    def members_by_role(self, role: ProjectRole) -> List[int]:
        """Project members' ids with at least required role (or higher)"""
        return [u.user_id for u in self.project_users if ProjectRole(u.role) >= role]

    def bulk_roles_update(self, access: Dict) -> Set[int]:
        """Update roles from access lists and return users ids of those affected by any action"""
        id_diffs = []
        for role in list(ProjectRole.__reversed__()):
            # we might not want to modify all roles
            if role not in access:
                continue

            for user_id in access.get(role):
                if self.get_role(user_id) != role:
                    self.set_role(user_id, role)
                    id_diffs.append(user_id)

            # make sure we do not have other user ids than in the list at this role
            for user in self.project_users:
                if ProjectRole(user.role) == role and user.user_id not in access.get(
                    role
                ):
                    self.unset_role(user.user_id)
                    id_diffs.append(user.user_id)

        return set(id_diffs)

    def get_delta_changes(
        self, since: int, to: int
    ) -> Optional[List[DeltaChangeMerged]]:
        """
        Get changes between two versions, merging them if needed.
        - create FileDiff checkpoints if needed
        - create ProjectVersionDelta checkpoints if needed with changes json
        """
        if since > to:
            logging.error(
                f"Start version {since} is higher than end version {to} - broken history"
            )
            return
        if since == to:
            return None
        project_id = self.id
        expected_checkpoints = Checkpoint.get_checkpoints(since + 1, to)
        expected_deltas: List[ProjectVersionDelta] = (
            ProjectVersionDelta.query.filter(
                ProjectVersionDelta.project_id == project_id,
                ProjectVersionDelta.version > since,
                ProjectVersionDelta.version <= to,
                tuple_(ProjectVersionDelta.rank, ProjectVersionDelta.version).in_(
                    [(item.rank, item.end) for item in expected_checkpoints]
                ),
            )
            .order_by(ProjectVersionDelta.version)
            .all()
        )
        existing_delta_map = {(c.rank, c.version): c for c in expected_deltas}

        result: List[DeltaChange] = []
        for checkpoint in expected_checkpoints:
            existing_delta = existing_delta_map.get((checkpoint.rank, checkpoint.end))

            # we have delta in database, just return delta data from it
            if existing_delta:
                result.extend(DeltaChangeSchema(many=True).load(existing_delta.changes))
                continue

            # If higher rank delta checkopoint does not exists we need to create it
            if checkpoint.rank > 0:
                new_checkpoint = ProjectVersionDelta.create_checkpoint(
                    project_id, checkpoint
                )
                if new_checkpoint:
                    result.extend(
                        DeltaChangeSchema(many=True).load(new_checkpoint.changes)
                    )
                else:
                    logging.error(
                        f"Not possible to create checkpoint for project {project_id} in range {checkpoint.start}-{checkpoint.end}"
                    )
                    return

        return ProjectVersionDelta.merge_changes(result)


class ProjectRole(Enum):
    """Project roles ordered by rank (do not change)"""

    READER = "reader"
    EDITOR = "editor"
    WRITER = "writer"
    OWNER = "owner"

    def __ge__(self, other):
        """Compare project roles"""
        members = list(ProjectRole.__members__)
        return members.index(self.name) >= members.index(other.name)

    def __gt__(self, other):
        members = list(ProjectRole.__members__)
        return members.index(self.name) > members.index(other.name)

    def __lt__(self, other):
        members = list(ProjectRole.__members__)
        return members.index(self.name) < members.index(other.name)


@dataclass
class ProjectMember:
    id: int
    email: str
    username: str
    workspace_role: WorkspaceRole
    project_role: Optional[ProjectRole]
    role: ProjectRole


@dataclass
class ProjectAccessDetail:
    id: int or str
    email: str
    role: str
    username: str
    name: Optional[str]
    workspace_role: str
    project_role: Optional[ProjectRole]
    type: str


class ProjectFilePath(db.Model):
    """Files (paths) within Project"""

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    path = db.Column(db.String, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("project_id", "path"),
        db.Index(
            "ix_project_file_path_project_id_path",
            project_id,
            path,
        ),
    )

    project = db.relationship(
        "Project",
        uselist=False,
    )

    def __init__(self, project_id, path):
        self.project_id = project_id
        self.path = path

    def generate_diff_name(self):
        """Generate uniqute diff file name for server generated diff"""
        return mergin_secure_filename(f"{self.path}-diff-{uuid.uuid4()}")


class LatestProjectFiles(db.Model):
    """Store project latest version files history ids"""

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
    )
    file_history_ids = db.Column(ARRAY(db.Integer), nullable=True)

    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref(
            "latest_project_files",
            single_parent=True,
            uselist=False,
            cascade="all,delete",
            lazy="select",
        ),
    )

    def __init__(self, project):
        self.project = project
        self.file_history_ids = []


class FileHistory(db.Model):
    """Changes for ProjectFilePath objects which happened in ProjectVersion"""

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    version_id = db.Column(
        db.Integer,
        db.ForeignKey("project_version.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # path on FS relative to project directory: version_name + file path
    location = db.Column(db.String)
    size = db.Column(db.BigInteger, nullable=False)
    checksum = db.Column(db.String, nullable=False)
    change = db.Column(
        ENUM(
            *PushChangeType.values(),
            name="push_change_type",
        ),
        index=True,
        nullable=False,
    )
    file_path_id = db.Column(
        db.BigInteger,
        db.ForeignKey("project_file_path.id", ondelete="CASCADE"),
        nullable=False,
    )
    # cache name of project version for more efficient queries
    project_version_name = db.Column(db.Integer, nullable=False)

    version = db.relationship(
        "ProjectVersion",
        uselist=False,
        backref=db.backref(
            "changes", single_parent=True, lazy="dynamic", cascade="all,delete"
        ),
    )

    file = db.relationship("ProjectFilePath", uselist=False)

    __table_args__ = (
        db.UniqueConstraint("version_id", "file_path_id"),
        db.Index(
            "ix_file_history_file_path_id_project_version_name",
            file_path_id,
            project_version_name.desc(),
        ),
    )

    def __init__(
        self,
        file: ProjectFilePath,
        size: int,
        checksum: str,
        location: str,
        change: PushChangeType,
        diff: dict = None,
        version_name: int = None,
    ):
        self.file = file
        self.size = size
        self.checksum = checksum
        self.location = location
        self.change = change.value
        self.project_version_name = version_name

        if diff is not None:
            basefile = FileHistory.get_basefile(file.id, version_name)
            diff_file = FileDiff(
                basefile=basefile,
                path=diff.get("path"),
                rank=0,
                version=version_name,
                size=diff.get("size"),
                checksum=diff.get("checksum"),
            )
            db.session.add(diff_file)

    @property
    def path(self) -> str:
        return self.file.path

    @property
    def diff(self) -> Optional[FileDiff]:
        """Diff file pushed with UPDATE_DIFF change type.

        In FileDiff table it is defined as diff related to file, saved for the same project version with rank 0 (elementar diff)
        """
        if self.change != PushChangeType.UPDATE_DIFF.value:
            return

        return FileDiff.query.filter_by(
            file_path_id=self.file_path_id, version=self.project_version_name, rank=0
        ).first()

    @property
    def diff_file(self) -> Optional[ProjectDiffFile]:
        if self.diff:
            return ProjectDiffFile(
                path=self.diff.path,
                size=self.diff.size,
                checksum=self.diff.checksum,
                location=self.diff.location,
            )

    @property
    def mtime(self) -> datetime:
        return self.version.created

    @property
    def abs_path(self) -> str:
        return os.path.join(self.version.project.storage.project_dir, self.location)

    @property
    def expiration(self) -> Optional[datetime]:
        if not self.diff_file:
            return

        if os.path.exists(self.abs_path):
            return datetime.utcfromtimestamp(
                os.path.getmtime(self.abs_path) + current_app.config["FILE_EXPIRATION"]
            )

    @classmethod
    def changes(
        cls, project_id: str, file: str, since: int, to: int, diffable: bool = False
    ) -> List[FileHistory]:
        """
        Returns file history (changes) between two versions. The result is ordered from the newest change.
        Actions for create and delete file are considered as a start of changes chain.

        If only versioned files are of interest (diffable=True) then forced update without diff is also considered
        as a start of changes chain.
        """
        if not (is_versioned_file(file) and since is not None and to is not None):
            return []

        history = []
        full_history = (
            FileHistory.query.join(ProjectFilePath)
            .filter(
                ProjectFilePath.project_id == project_id,
                FileHistory.project_version_name <= to,
                FileHistory.project_version_name >= since,
                ProjectFilePath.path == file,
            )
            .order_by(desc(FileHistory.project_version_name))
            .all()
        )

        for item in full_history:
            history.append(item)

            # end of file history
            if item.change in [
                PushChangeType.CREATE.value,
                PushChangeType.DELETE.value,
            ]:
                break

            # if we are interested only in 'diffable' history (not broken with forced update)
            if diffable and item.change == PushChangeType.UPDATE.value:
                break

        return history

    @classmethod
    def diffs_chain(
        cls, file_id: int, version: int
    ) -> Tuple[Optional[FileHistory], List[Optional[FileDiff]]]:
        """Find chain of diffs from the basefile that leads to a given file at certain project version.

        Returns basefile and list of diffs for gpkg that needs to be applied to reconstruct file.
        List of diffs can be empty if basefile was eventually asked. Basefile can be empty if file cannot be
        reconstructed (removed/renamed).
        """
        latest_change = (
            cls.query.filter_by(file_path_id=file_id)
            .filter(cls.project_version_name <= version)
            .order_by(desc(cls.project_version_name))
            .first()
        )
        # file never existed prior that version
        if not latest_change:
            return None, []

        # the last update to file was a delete
        if latest_change.change == PushChangeType.DELETE.value:
            return None, []

        # the last update to file was a create / force update
        if latest_change.change in (
            PushChangeType.CREATE.value,
            PushChangeType.UPDATE.value,
        ):
            return latest_change, []

        basefile = cls.get_basefile(file_id, version)
        if not basefile:
            return None, []

        diffs = []
        cached_items = Checkpoint.get_checkpoints(
            basefile.project_version_name, version
        )
        expected_diffs = (
            FileDiff.query.filter_by(
                basefile_id=basefile.id,
            )
            .filter(
                tuple_(FileDiff.rank, FileDiff.version).in_(
                    [(item.rank, item.end) for item in cached_items]
                )
            )
            .all()
        )

        for item in cached_items:
            diff = next(
                (
                    d
                    for d in expected_diffs
                    if d.rank == item.rank and d.version == item.end
                ),
                None,
            )
            if diff and os.path.exists(diff.abs_path):
                diffs.append(diff)
            elif item.rank > 0:
                # fallback if checkpoint does not exist: replace merged diff with individual diffs
                individual_diffs = (
                    FileDiff.query.filter_by(
                        basefile_id=basefile.id,
                        rank=0,
                    )
                    .filter(
                        FileDiff.version >= item.start, FileDiff.version <= item.end
                    )
                    .order_by(FileDiff.version)
                    .all()
                )
                diffs.extend(individual_diffs)
            else:
                # we asked for individual diff but there is no such diff as there was not change at that version
                continue

        return basefile, diffs

    @classmethod
    def get_basefile(cls, file_path_id: int, version: int) -> Optional[FileHistory]:
        """Get basefile (start of file diffable history) for diff file change at some version"""
        return (
            cls.query.filter_by(file_path_id=file_path_id)
            .filter(
                cls.project_version_name < version,
                cls.change.in_(
                    [PushChangeType.CREATE.value, PushChangeType.UPDATE.value]
                ),
            )
            .order_by(desc(cls.project_version_name))
            .first()
        )


class FileDiff(db.Model):
    """File diffs related to versioned files, also contain higher order (rank) merged diffs"""

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    file_path_id = db.Column(
        db.BigInteger,
        db.ForeignKey("project_file_path.id", ondelete="CASCADE"),
        nullable=False,
    )
    # reference to actual full gpkg file
    basefile_id = db.Column(
        db.BigInteger,
        db.ForeignKey("file_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    path = db.Column(db.String, nullable=False, index=True)
    # exponential order of merged diff, 0 is a source diff file uploaded by user, > 0 is merged diff
    rank = db.Column(db.Integer, nullable=False, index=True)
    # to which project version is this linked
    version = db.Column(db.Integer, nullable=False, index=True)
    # path on FS relative to project directory
    location = db.Column(db.String)
    # size and checksum are nullable as for merged diffs (higher orders) they might not exist on disk yet
    size = db.Column(db.BigInteger, nullable=True)
    checksum = db.Column(db.String, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("file_path_id", "rank", "version", name="unique_diff"),
        db.Index("ix_file_diff_file_path_id_version_rank", file_path_id, version, rank),
    )

    file = db.relationship("ProjectFilePath", uselist=False)

    def __init__(
        self,
        basefile: FileHistory,
        path: str,
        rank: int,
        version: int,
        size: int = None,
        checksum: str = None,
    ):
        self.basefile_id = basefile.id
        self.file_path_id = basefile.file_path_id
        self.path = path
        self.size = size
        self.checksum = checksum
        self.rank = rank
        self.version = version
        self.location = (
            os.path.join("diffs", path)
            if rank > 0
            else os.path.join(f"v{version}", path)
        )

    @property
    def abs_path(self) -> str:
        """
        Return absolute path of the diff file on the file system.
        """
        return os.path.join(self.file.project.storage.project_dir, self.location)

    @staticmethod
    def can_create_checkpoint(file_path_id: int, checkpoint: Checkpoint) -> bool:
        """Check if it makes sense to create a diff file for a checkpoint, e.g. there were relevant changes within the range without breaking changes"""

        basefile = FileHistory.get_basefile(file_path_id, checkpoint.end)
        if not basefile:
            return False

        file_was_deleted = (
            FileHistory.query.filter_by(file_path_id=file_path_id)
            .filter(
                FileHistory.project_version_name
                >= max(basefile.project_version_name, checkpoint.start),
                FileHistory.project_version_name <= checkpoint.end,
                FileHistory.change == PushChangeType.DELETE.value,
            )
            .count()
            > 0
        )
        if file_was_deleted:
            return False

        query = FileDiff.query.filter_by(basefile_id=basefile.id).filter(
            FileDiff.rank == 0
        )

        # rank 0 is a special case we only verify it exists
        if checkpoint.rank == 0:
            query = query.filter(FileDiff.version == checkpoint.end)
        # for higher ranks we need to check if there were diff updates in that range
        else:
            query = query.filter(
                FileDiff.version >= checkpoint.start,
                FileDiff.version <= checkpoint.end,
            )

        return query.count() > 0

    def construct_checkpoint(self) -> bool:
        """Create a diff file checkpoint (aka. merged diff).
        Find all smaller diffs which are needed to create the final diff file and merge them.
        In case of missing some lower rank checkpoints, create them recursively.

        Once checkpoint is created, size and checksum are updated in the database.

        Returns:
            bool: True if checkpoint was successfully created or already present
        """
        logging.debug(
            f"Construct checkpoint for file {self.path} v{self.version} of rank {self.rank}"
        )

        if os.path.exists(self.abs_path):
            return True

        # merged diffs can only be created for certain versions
        if self.version % LOG_BASE:
            return False

        cache_level_index = self.version // LOG_BASE**self.rank
        try:
            cache_level = Checkpoint(rank=self.rank, index=cache_level_index)
        except ValueError:
            logging.error(
                f"Invalid record for cached level of rank {self.rank} and index {cache_level_index} for file {self.file_path_id}"
            )
            return False

        basefile = FileHistory.get_basefile(self.file_path_id, cache_level.end)
        if not basefile:
            logging.error(f"Unable to find basefile for file {self.file_path_id}")
            return False

        if basefile.project_version_name > cache_level.start:
            logging.error(
                f"Basefile version {basefile.project_version_name} is higher than start version {cache_level.start} - broken history"
            )
            return False

        diffs_paths = []
        # let's confirm we have all intermediate diffs needed, if not, we need to create them (recursively) first
        cached_items = Checkpoint.get_checkpoints(
            cache_level.start, cache_level.end - 1
        )
        expected_diffs = (
            FileDiff.query.filter_by(
                basefile_id=basefile.id,
            )
            .filter(
                tuple_(FileDiff.rank, FileDiff.version).in_(
                    [(item.rank, item.end) for item in cached_items]
                )
            )
            .all()
        )

        for item in cached_items:
            # basefile is a start of the diff chain
            if item.start <= basefile.project_version_name:
                continue

            # find diff in table and on disk
            # diffs might not exist because theye were not created yet or there were no changes (e.g. for zeroth rank diffs)
            diff = next(
                (
                    d
                    for d in expected_diffs
                    if d.rank == item.rank and d.version == item.end
                ),
                None,
            )

            if not diff:
                # lower rank diff not even in DB yet - create it and try to construct merged file
                if item.rank > 0 and FileDiff.can_create_checkpoint(
                    self.file_path_id, item
                ):
                    diff = FileDiff(
                        basefile=basefile,
                        version=item.end,
                        rank=item.rank,
                        path=basefile.file.generate_diff_name(),
                        size=None,
                        checksum=None,
                    )
                    db.session.add(diff)
                    db.session.commit()
                else:
                    # such diff is not expected to exist
                    continue

            diff_exists = diff.construct_checkpoint()
            if diff_exists:
                diffs_paths.append(diff.abs_path)
            else:
                logging.error(
                    f"Unable to create checkpoint diff for {item} for file {self.file_path_id}"
                )
                return False

        # we apply latest change (if any) on previous version
        end_diff = FileDiff.query.filter_by(
            basefile_id=basefile.id,
            rank=0,
            version=cache_level.end,
        ).first()

        if end_diff:
            diffs_paths.append(end_diff.abs_path)

        if not diffs_paths:
            logging.warning(
                f"No diffs for next checkpoint for file {self.file_path_id}"
            )
            return False

        project: Project = basefile.file.project
        os.makedirs(project.storage.diffs_dir, exist_ok=True)
        try:
            project.storage.geodiff.concat_changes(diffs_paths, self.abs_path)
        except (GeoDiffLibError, GeoDiffLibConflictError):
            logging.error(
                f"Geodiff: Failed to merge diffs for file {self.file_path_id}"
            )
            return False

        self.size = os.path.getsize(self.abs_path)
        self.checksum = generate_checksum(self.abs_path)
        db.session.commit()
        return True


class ProjectVersionDelta(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    version = db.Column(db.Integer, nullable=False, index=True)
    # exponential order of changes json
    rank = db.Column(db.Integer, nullable=False, index=True)
    # to which project is this linked
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # cached changes for versions from start to end (inclusive)
    changes = db.Column(JSONB, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("project_id", "version", "rank", name="unique_deltas"),
        db.Index(
            "ix_project_version_delta_project_id_version_rank",
            project_id,
            version,
            rank,
        ),
    )
    project = db.relationship(
        "Project",
        uselist=False,
    )

    @staticmethod
    def merge_changes(
        items: List[DeltaChange],
    ) -> List[DeltaChangeMerged]:
        """
        Merge changes json array objects into one list of changes.
        Changes are merged based on file path and change type.
        """
        updating_files: Set[str] = set()
        # sorting changes by version to apply them in correct order
        items.sort(key=lambda x: x.version)

        # Merge changes for each file in a single pass
        result: Dict[str, DeltaChangeMerged] = {}
        for item in items:
            path = item.path
            current = item.to_merged()

            # First change for this file
            if path not in result:
                result[path] = current
                # track existing paths to avoid deleting files that are already in history before
                if current.change != PushChangeType.CREATE:
                    updating_files.add(path)
                continue

            # Compare and merge with previous change for this file
            can_delete = path in updating_files
            new_change = ProjectVersionDelta._compare_changes(
                result[path], current, can_delete
            )

            # Update result (or remove if no change is detected)
            if new_change is not None:
                result[path] = new_change
            else:
                del result[path]

        return list(result.values())

    @staticmethod
    def _compare_changes(
        previous: DeltaChangeMerged,
        new: DeltaChangeMerged,
        prevent_delete_change: bool,
    ) -> Optional[DeltaChangeMerged]:
        """
        Compare and merge two changes for the same file.

        Args:
            previous: Previously accumulated change
            new: New change to compare
            prevent_delete_change: Whether the change can be deleted when resolving create+delete sequences

        Returns:
            Merged change or None if file should be excluded
        """

        # Map change type pairs to actions
        action_map = {
            # create + delete = file is transparent for current changes -> delete it
            (
                PushChangeType.CREATE,
                PushChangeType.DELETE,
            ): ChangeComparisonAction.DELETE,
            # create + update = create with updated info
            (
                PushChangeType.CREATE,
                PushChangeType.UPDATE,
            ): ChangeComparisonAction.UPDATE,
            (
                PushChangeType.CREATE,
                PushChangeType.UPDATE_DIFF,
            ): ChangeComparisonAction.UPDATE,
            (
                PushChangeType.CREATE,
                PushChangeType.CREATE,
            ): ChangeComparisonAction.EXCLUDE,
            # update + update_diff = update with latest info
            (
                PushChangeType.UPDATE,
                PushChangeType.UPDATE_DIFF,
            ): ChangeComparisonAction.UPDATE,
            (
                PushChangeType.UPDATE,
                PushChangeType.UPDATE,
            ): ChangeComparisonAction.REPLACE,
            (
                PushChangeType.UPDATE,
                PushChangeType.DELETE,
            ): ChangeComparisonAction.REPLACE,
            (
                PushChangeType.UPDATE,
                PushChangeType.CREATE,
            ): ChangeComparisonAction.REPLACE,
            # update_diff + update_diff = update_diff with latest info with proper order of diffs
            (
                PushChangeType.UPDATE_DIFF,
                PushChangeType.UPDATE_DIFF,
            ): ChangeComparisonAction.UPDATE_DIFF,
            (
                PushChangeType.UPDATE_DIFF,
                PushChangeType.UPDATE,
            ): ChangeComparisonAction.REPLACE,
            (
                PushChangeType.UPDATE_DIFF,
                PushChangeType.DELETE,
            ): ChangeComparisonAction.REPLACE,
            (
                PushChangeType.UPDATE_DIFF,
                PushChangeType.CREATE,
            ): ChangeComparisonAction.EXCLUDE,
            (
                PushChangeType.DELETE,
                PushChangeType.CREATE,
            ): ChangeComparisonAction.REPLACE,
            # delete + update = invalid sequence
            (
                PushChangeType.DELETE,
                PushChangeType.UPDATE,
            ): ChangeComparisonAction.EXCLUDE,
            (
                PushChangeType.DELETE,
                PushChangeType.UPDATE_DIFF,
            ): ChangeComparisonAction.EXCLUDE,
            (
                PushChangeType.DELETE,
                PushChangeType.DELETE,
            ): ChangeComparisonAction.EXCLUDE,
        }

        action = action_map.get((previous.change, new.change))
        result = None
        if action == ChangeComparisonAction.REPLACE:
            result = new

        elif action == ChangeComparisonAction.DELETE:
            # if change is create + delete, we can just remove the change from accumulated changes
            # only if this action is allowed (file existed before)
            if prevent_delete_change:
                result = new

        elif action == ChangeComparisonAction.UPDATE:
            # handle update case, when previous change was create - just revert to create with new metadata
            new.change = previous.change
            new.diffs = []
            result = new

        elif action == ChangeComparisonAction.UPDATE_DIFF:
            new.diffs = (previous.diffs or []) + (new.diffs or [])
            result = new

        return result

    @classmethod
    def create_checkpoint(
        cls,
        project_id: str,
        checkpoint: Checkpoint,
    ) -> Optional[ProjectVersionDelta]:
        """
        Creates and caches new checkpoint and any required FileDiff checkpoints recursively if needed.
        """
        delta_range = []
        # our new checkpoint will be created by adding last individual delta to previous checkpoints
        expected_checkpoints = Checkpoint.get_checkpoints(
            checkpoint.start, checkpoint.end - 1
        )
        expected_checkpoints.append(Checkpoint(rank=0, index=checkpoint.end))

        expected_deltas = (
            ProjectVersionDelta.query.filter(
                ProjectVersionDelta.project_id == project_id,
                tuple_(ProjectVersionDelta.rank, ProjectVersionDelta.version).in_(
                    [(item.rank, item.end) for item in expected_checkpoints]
                ),
            )
            .order_by(ProjectVersionDelta.version)
            .all()
        )

        existing_delta_map = {(c.rank, c.version): c for c in expected_deltas}
        # make sure we have all components, if not, created them (recursively)
        for item in expected_checkpoints:
            existing_delta = existing_delta_map.get((item.rank, item.end))
            if not existing_delta:
                existing_delta = cls.create_checkpoint(project_id, item)

            if existing_delta:
                delta_range.append(existing_delta)
            else:
                logging.error(
                    f"Missing project delta endpoint for {project_id} v{item.end} rank {item.rank} which could not be recreated"
                )
                return

        if not delta_range:
            logging.warning(
                f"No changes found for project {project_id} in range v{checkpoint.start}-v{checkpoint.end} to create checkpoint."
            )
            return None

        # dump changes lists from database and flatten list for merging
        delta_range = sorted(delta_range, key=lambda x: x.version)
        changes = []
        for delta in delta_range:
            changes.extend(DeltaChangeSchema(many=True).load(delta.changes))
        merged_delta_items: List[DeltaChange] = [
            d.to_data_delta() for d in cls.merge_changes(changes)
        ]

        # Pre-fetch data for all versioned files to create FileDiff checkpoints where it makes sense
        versioned_delta_items = [
            item
            for item in merged_delta_items
            if is_versioned_file(item.path)
            and item.change == PushChangeType.UPDATE_DIFF
        ]
        versioned_file_paths = [delta.path for delta in versioned_delta_items]
        if versioned_file_paths:
            # get versioned files from DB and lookup their paths to next processing
            file_paths = ProjectFilePath.query.filter(
                ProjectFilePath.project_id == project_id,
                ProjectFilePath.path.in_(versioned_file_paths),
            ).all()
            file_path_map = {fp.path: fp.id for fp in file_paths}

            for item in versioned_delta_items:
                file_path_id = file_path_map.get(item.path)
                if not file_path_id:
                    continue

                # Check if a FileDiff checkpoint already exists
                existing_diff_checkpoint = FileDiff.query.filter_by(
                    file_path_id=file_path_id,
                    rank=checkpoint.rank,
                    version=checkpoint.end,
                ).first()
                # If does not exists, let's create diff with higher rank and some generated path (name of diff file)
                if not existing_diff_checkpoint:
                    base_file = FileHistory.get_basefile(file_path_id, checkpoint.end)
                    if not base_file:
                        continue

                    if not FileDiff.can_create_checkpoint(file_path_id, checkpoint):
                        continue

                    checkpoint_diff = FileDiff(
                        basefile=base_file,
                        path=base_file.file.generate_diff_name(),
                        rank=checkpoint.rank,
                        version=checkpoint.end,
                    )
                    # Patch the delta with the path to the new diff checkpoint
                    item.diff = checkpoint_diff.path
                    db.session.add(checkpoint_diff)

        checkpoint_delta = ProjectVersionDelta(
            project_id=project_id,
            version=checkpoint.end,
            rank=checkpoint.rank,
            changes=DeltaChangeSchema(many=True).dump(merged_delta_items),
        )
        db.session.add(checkpoint_delta)
        db.session.commit()
        return checkpoint_delta


class ProjectVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Integer, index=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), index=True, nullable=True
    )
    user_agent = db.Column(db.String, index=True)
    ip_address = db.Column(db.String, index=True)
    ip_geolocation_country = db.Column(
        db.String, index=True
    )  # geolocation country derived from IP (with celery job)
    project_size = db.Column(
        BIGINT, nullable=False, default=0, index=True
    )  # size of project at current version (incl. files from older versions)
    project = db.relationship(
        "Project",
        uselist=False,
    )
    device_id = db.Column(db.String, index=True, nullable=True)
    author = db.relationship("User", uselist=False, lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("project_id", "name"),
        db.Index(
            "ix_project_version_project_id_name",
            project_id,
            nullslast(name.asc()),
        ),
    )

    def __init__(
        self,
        project: Project,
        name: int,
        author_id: int,
        changes: List[ProjectFileChange],
        ip: str,
        user_agent: str = None,
        device_id: str = None,
    ):
        self.project = project
        self.project_id = project.id
        self.name = name
        self.author_id = author_id
        self.user_agent = user_agent
        self.ip_address = ip
        self.device_id = device_id

        latest_files_map = {
            fh.path: fh.id
            for fh in FileHistory.query.filter(
                FileHistory.id.in_(self.project.latest_project_files.file_history_ids)
            ).all()
        }

        changed_files_paths = set(change.path for change in changes)
        existing_files_map = {
            f.path: f
            for f in ProjectFilePath.query.filter_by(project_id=self.project_id)
            .filter(ProjectFilePath.path.in_(changed_files_paths))
            .all()
        }
        for item in changes:
            # get existing DB file reference or create a new one (for added files)
            db_file = existing_files_map.get(
                item.path, ProjectFilePath(self.project_id, item.path)
            )
            fh = FileHistory(
                file=db_file,
                size=item.size,
                checksum=item.checksum,
                location=item.location,
                diff=(
                    asdict(item.diff)
                    if (item.change is PushChangeType.UPDATE_DIFF and item.diff)
                    else None
                ),
                change=item.change,
                version_name=self.name,
            )
            fh.version = self
            fh.project_version_name = self.name
            db.session.add(fh)
            db.session.flush()

            if item.change is PushChangeType.DELETE:
                latest_files_map.pop(fh.path, None)
            else:
                latest_files_map[fh.path] = fh.id

        # cache changes data json for version checkpoints
        # rank 0 is for all changes from start to current version
        delta_data = [
            DeltaChange(
                path=c.path,
                change=c.change,
                size=c.size,
                checksum=c.checksum,
                version=name,
                diff=c.diff.path if c.diff else None,
            )
            for c in changes
        ]
        pvd = ProjectVersionDelta(
            project_id=project.id,
            version=name,
            rank=0,
            changes=DeltaChangeSchema(many=True).dump(delta_data),
        )

        db.session.add(pvd)
        db.session.flush()

        # update cached values in project and push to transaction buffer so that self.files is up-to-date
        self.project.latest_project_files.file_history_ids = latest_files_map.values()
        db.session.flush()
        self.project.disk_usage = (
            sum(f.size for f in self.project.files) if self.project.files else 0
        )
        self.project.latest_version = self.name
        self.project.tags = self.resolve_tags()
        self.project_size = self.project.disk_usage
        db.session.flush()

    @staticmethod
    def from_v_name(name: str) -> int:
        """Parsed version name as integer (v5 -> 5)"""
        return int(name.strip().replace("v", ""))

    @staticmethod
    def to_v_name(name: int) -> str:
        """Parsed version name as string with prefix (5 -> v5)
        Used in public API and as part of file path on FS.
        """
        return "v" + str(name)

    def _files_from_start(self):
        """Calculate version files using lookup from the first version
        Strategy: From all project files get the latest file change before or at the specific version.
        If that change was not 'delete', file is present.
        """
        query = f"""
            WITH latest_changes AS (
                SELECT
                    fp.id,
                    max(pv.name) AS version
                FROM
                    project_version pv
                LEFT OUTER JOIN file_history fh ON fh.version_id = pv.id
                LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
                WHERE
                    pv.project_id = :project_id
                    AND pv.name <= :version
                GROUP BY
                    fp.id
            )
            SELECT
                fp.path,
                fh.size,
                fh.location,
                fh.checksum,
                pv.created AS mtime,
                fd.path as diff_path,
                fd.size as diff_size,
                fd.checksum as diff_checksum,
                fd.location as diff_location
            FROM latest_changes ch
            LEFT OUTER JOIN file_history fh ON (fh.file_path_id = ch.id AND fh.project_version_name = ch.version)
            LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
            LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
            LEFT OUTER JOIN file_diff fd ON fd.file_path_id = fh.file_path_id AND fd.version = fh.project_version_name and fd.rank = 0
            WHERE fh.change != 'delete';
        """
        params = {"project_id": self.project_id, "version": self.name}
        return db.session.execute(text(query), params).fetchall()

    def _files_from_end(self):
        """Calculate version files using lookup from the last version
        Strategy: Get project files which could be present at specific version. These are either latest files or
        files that were delete after the version (and thus not necessarily present now). From these candidates
        get the latest file change before or at the specific version. If that change was not 'delete', file is present.
        """
        query = f"""
            WITH files_changes_before_version AS (
                WITH files_candidates AS (
                    -- files removed later (but created anytime)
                    SELECT DISTINCT
                        fh.file_path_id AS file_id
                    FROM project_version pv
                    LEFT OUTER JOIN file_history fh ON fh.version_id = pv.id
                    WHERE
                        pv.project_id = :project_id
                        AND pv.name > :version
                        AND fh.change = 'delete'
                    -- union with current files
                    UNION
                    SELECT
                        fh.file_path_id AS file_id
                    FROM file_history fh
                    WHERE fh.id IN (
                        SELECT unnest(file_history_ids)
                        FROM latest_project_files
                        WHERE project_id = :project_id
                    )
                )
                SELECT
                    fs.file_id,
                    max(fh.project_version_name) AS version
                FROM files_candidates fs
                -- there can be candidates which do not have records in earlier versions
                INNER JOIN file_history fh ON fh.file_path_id = fs.file_id
                WHERE
                    fh.project_version_name <= :version
                GROUP BY
                    fs.file_id
            )
            SELECT
                fp.path,
                fh.size,
                fh.location,
                fh.checksum,
                pv.created AS mtime,
                fd.path as diff_path,
                fd.size as diff_size,
                fd.checksum as diff_checksum,
                fd.location as diff_location
            FROM files_changes_before_version ch
            INNER JOIN file_history fh ON (fh.file_path_id = ch.file_id AND fh.project_version_name = ch.version)
            INNER JOIN project_file_path fp ON fp.id = fh.file_path_id
            INNER JOIN project_version pv ON pv.id = fh.version_id
            LEFT OUTER JOIN file_diff fd ON fd.file_path_id = fh.file_path_id AND fd.version = fh.project_version_name and fd.rank = 0
            WHERE fh.change != 'delete'
            ORDER BY fp.path;
        """
        params = {"project_id": self.project_id, "version": self.name}
        return db.session.execute(text(query), params).fetchall()

    @property
    def files(self) -> List[ProjectFile]:
        # return from cache
        if self.name == self.project.latest_version:
            return self.project.files

        if self.name < self.project.latest_version / 2:
            result = self._files_from_start()
        else:
            result = self._files_from_end()
        files = [
            ProjectFile(
                path=row.path,
                size=row.size,
                checksum=row.checksum,
                location=row.location,
                mtime=row.mtime,
                diff=(
                    ProjectDiffFile(
                        path=row.diff_path,
                        checksum=row.diff_checksum,
                        size=row.diff_size,
                        location=row.diff_location,
                    )
                    if row.diff_path
                    else None
                ),
            )
            for row in result
        ]
        return files

    def resolve_tags(self) -> List[str]:
        tags = []
        qgis_count = 0
        for f in self.files:
            if is_qgis(f.path):
                qgis_count += 1
        if qgis_count == 1:
            tags.extend(["valid_qgis", "input_use"])
        return tags

    def diff_summary(self):
        """Calculate diff summary for versioned files updated with geodiff

        :Example:

        >>> self.diff_summary()
        {
          'base.gpkg': {
            'summary': [
              {'table': 'gpkg_contents', 'insert': 0, 'update': 1, 'delete': 0},
              {'table': 'simple', 'insert': 2, 'update': 0, 'delete': 0}
            ],
            'size': 278
          },
          'fail.gpkg': {
            'error': 'some geodiff error',
            'size': 278
          }
        }

        :return: diffs' summaries for all updated files
        :rtype: dict
        """
        output = {}
        self.project.storage.flush_geodiff_logger()
        for f in self.changes.all():
            if f.change != PushChangeType.UPDATE_DIFF.value:
                continue

            json_file = os.path.join(
                self.project.storage.project_dir, f.location + "-diff-summary"
            )
            changeset = os.path.join(
                self.project.storage.project_dir, f.diff_file.location
            )
            if not os.path.exists(json_file):
                try:
                    self.project.storage.geodiff.list_changes_summary(
                        changeset, json_file
                    )
                except GeoDiffLibError:
                    output[f.path] = {
                        "error": self.project.storage.gediff_log.getvalue(),
                        "size": f.diff_file.size,
                    }
                    continue
            with open(json_file, "r") as jf:
                content = json.load(jf)
                if "geodiff_summary" not in content:
                    continue

                output[f.path] = {
                    "summary": content["geodiff_summary"],
                    "size": f.diff_file.size,
                }

        return output

    def changes_count(self) -> Dict:
        """Return number of changes by type"""
        query = f"SELECT change, COUNT(change) FROM file_history WHERE version_id = :version_id GROUP BY change;"
        params = {"version_id": self.id}
        result = db.session.execute(text(query), params).fetchall()
        return {row[0]: row[1] for row in result}

    @property
    def zip_path(self):
        return os.path.join(
            current_app.config["PROJECTS_ARCHIVES_DIR"],
            f"{self.project_id}-{self.to_v_name(self.name)}.zip",
        )


class Upload(db.Model):
    id = db.Column(db.String, primary_key=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    # project version where upload is initiated from
    version = db.Column(db.Integer, index=True)
    changes = db.Column(db.JSON)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref(
            "uploads", single_parent=True, lazy="dynamic", cascade="all,delete"
        ),
    )
    __table_args__ = (db.UniqueConstraint("project_id", "version"),)

    def __init__(self, project: Project, version: int, changes: dict, user_id: int):
        self.id = str(uuid.uuid4())
        self.project_id = project.id
        self.version = version
        self.changes = ChangesSchema().dump(changes)
        self.user_id = user_id

    @property
    def upload_dir(self):
        return os.path.join(self.project.storage.project_dir, "tmp", self.id)

    @property
    def lockfile(self):
        return os.path.join(self.upload_dir, "lockfile")

    def is_active(self):
        """Check if upload is still active because there was a ping (lockfile update) from underlying process"""
        return os.path.exists(self.lockfile) and (
            time.time() - os.path.getmtime(self.lockfile)
            < current_app.config["LOCKFILE_EXPIRATION"]
        )

    def clear(self):
        """Clean up pending upload.
        Uploaded files and table records are removed, and another upload can start.
        """
        move_to_tmp(self.upload_dir, self.id)
        db.session.delete(self)
        db.session.commit()

    def process_chunks(
        self, use_shared_chunk_dir: bool
    ) -> Tuple[List[ProjectFileChange], Dict]:
        """Concatenate chunks into single file and apply gpkg updates if needed"""
        errors = {}
        project_path = get_project_path(self.project)
        v_next_version = ProjectVersion.to_v_name(self.project.next_version())
        chunks_map = {
            f["path"]: f["chunks"]
            for f in self.changes["added"] + self.changes["updated"]
        }
        file_changes = files_changes_from_upload(self.changes, v_next_version)
        to_remove = [i.path for i in file_changes if i.change == PushChangeType.DELETE]
        current_files = [f for f in self.project.files if f.path not in to_remove]

        with Toucher(self.lockfile, 5):
            for f in file_changes:
                if f.change == PushChangeType.DELETE:
                    continue

                f_location = (
                    f.diff.location
                    if f.change == PushChangeType.UPDATE_DIFF
                    else f.location
                )
                temporary_location = os.path.join(self.upload_dir, "files", f_location)
                os.makedirs(os.path.dirname(temporary_location), exist_ok=True)
                with open(temporary_location, "wb") as dest:
                    try:
                        for chunk_id in chunks_map.get(f.path, []):
                            # based on API version location for uploaded chunks differs
                            if use_shared_chunk_dir:
                                chunk_file = get_chunk_location(chunk_id)
                            else:
                                chunk_file = os.path.join(
                                    self.upload_dir, "chunks", chunk_id
                                )

                            if not os.path.exists(chunk_file):
                                errors[f.path] = FileSyncErrorType.CORRUPTED.value
                                continue

                            with open(chunk_file, "rb") as src:
                                data = src.read(8192)
                                while data:
                                    dest.write(data)
                                    data = src.read(8192)

                    except IOError:
                        logging.exception(
                            f"Failed to process chunk: {chunk_id} in project {project_path}"
                        )
                        errors[f.path] = FileSyncErrorType.CORRUPTED.value
                        continue

                if (
                    not f.change == PushChangeType.UPDATE_DIFF
                    and not is_supported_type(temporary_location)
                ):
                    logging.info(f"Rejecting blacklisted file: {temporary_location}")
                    errors[f.path] = FileSyncErrorType.UNSUPPORTED.value
                    continue

                # check if .gpkg file is valid
                if is_versioned_file(temporary_location) and not f.is_valid_gpkg():
                    errors[f.path] = FileSyncErrorType.CORRUPTED.value
                    continue

                expected_size = (
                    f.diff.size if f.change == PushChangeType.UPDATE_DIFF else f.size
                )
                if expected_size != os.path.getsize(temporary_location):
                    logging.error(
                        f"Data integrity check has failed on file {f.path} in project {project_path}",
                        exc_info=True,
                    )
                    errors[f.path] = FileSyncErrorType.CORRUPTED.value
                    continue

                # for updates try to apply diff to create a full updated gpkg file or from full .gpkg try to create corresponding diff
                if f.change in (
                    PushChangeType.UPDATE,
                    PushChangeType.UPDATE_DIFF,
                ) and is_versioned_file(f.path):
                    current_file = next(
                        (i for i in current_files if i.path == f.path), None
                    )
                    if not current_file:
                        errors[f.path] = (
                            f"{FileSyncErrorType.SYNC_ERROR.value}: file not found on server"
                        )
                        continue

                    if f.diff:
                        changeset = temporary_location
                        patched_file = os.path.join(
                            self.upload_dir, "files", f.location
                        )

                        result = self.project.storage.apply_diff(
                            current_file, changeset, patched_file
                        )
                        if result.ok():
                            checksum, size = result.value
                            f.checksum = checksum
                            f.size = size
                        else:
                            errors[f.path] = (
                                f"{FileSyncErrorType.SYNC_ERROR.value}: project {self.project.workspace.name}/{self.project.name}, {result.value}"
                            )
                    else:
                        diff_name = mergin_secure_filename(
                            f.path + "-diff-" + str(uuid.uuid4())
                        )
                        changeset = os.path.join(
                            self.upload_dir, "files", v_next_version, diff_name
                        )
                        patched_file = temporary_location
                        result = self.project.storage.construct_diff(
                            current_file, changeset, patched_file
                        )
                        if result.ok():
                            checksum, size = result.value
                            f.diff = ProjectDiffFile(
                                checksum=checksum,
                                size=size,
                                path=diff_name,
                                location=os.path.join(v_next_version, diff_name),
                            )
                            f.change = PushChangeType.UPDATE_DIFF
                        else:
                            # if diff cannot be constructed it would be a force update
                            logging.warning(
                                f"Geodiff: create changeset error {result.value}"
                            )
        return file_changes, errors


class RequestStatus(Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]


class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    requested_by = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    requested_at = db.Column(
        db.DateTime, default=datetime.utcnow, index=True, nullable=False
    )
    resolved_by = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    resolved_at = db.Column(db.DateTime, nullable=True, index=True)
    # how request was resolved: accepted / declined
    status = db.Column(
        ENUM(*RequestStatus.values(), name="request_status"), nullable=True, index=True
    )

    project = db.relationship("Project", uselist=False)

    def __init__(self, project, user_id):
        self.project_id = project.id
        self.requested_by = user_id

    @property
    def expire(self):
        return self.requested_at + timedelta(
            seconds=current_app.config["PROJECT_ACCESS_REQUEST"]
        )

    def accept(self, permissions):
        """Accept project access request"""
        PERMISSION_PROJECT_ROLE = {
            "read": ProjectRole.READER,
            "edit": ProjectRole.EDITOR,
            "write": ProjectRole.WRITER,
            "owner": ProjectRole.OWNER,
        }

        self.project.set_role(
            self.requested_by, PERMISSION_PROJECT_ROLE.get(permissions)
        )
        self.resolve(RequestStatus.ACCEPTED, current_user.id)
        db.session.commit()

    def resolve(self, status: RequestStatus, resolved_by=None):
        """Resolve request"""
        self.status = status.value
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()


class SyncFailuresHistory(db.Model):
    """DB model for tracking (outside of mergin) project sync failures
    Model is only loosely coupled with Project, so even if project is gone, history of failures remains.
    """

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(UUID(as_uuid=True), index=True)  # cached value
    last_version = db.Column(db.String, index=True)
    user_agent = db.Column(db.String, index=True)
    error_type = db.Column(
        db.String, index=True
    )  # e.g. push_start, push_finish, push_lost
    error_details = db.Column(db.String)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    def __init__(self, project, ua, err_type, err_details, user_id):
        self.user_agent = ua
        self.error_type = err_type
        self.error_details = err_details
        self.project_id = project.id
        self.last_version = ProjectVersion.to_v_name(project.latest_version)
        self.user_id = user_id


class GeodiffActionHistory(db.Model):
    """DB model for tracking (outside of mergin) use of geodiff use history, particularly Geodiff.apply_changeset action.
    This might involve other tasks like copying basefile and target files over.

    Model is only loosely coupled with Project, so even if project is gone, history remains.
    """

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        UUID(as_uuid=True), nullable=False, index=True
    )  # cached value
    base_version = db.Column(db.String, nullable=False)
    target_version = db.Column(db.String, nullable=False)
    file_name = db.Column(
        db.String, nullable=False, index=True
    )  # relative path of file in project
    file_size = db.Column(BIGINT)  # in bytes
    diff_size = db.Column(db.Integer)  # in bytes
    changes = db.Column(db.Integer)  # number of changes in diff
    action = db.Column(db.String, index=True)  # flask action where geodiff was used
    # these fields are known only after action is performed
    copy_time = db.Column(db.Float)  # in seconds
    checksum_time = db.Column(db.Float)  # in seconds
    geodiff_time = db.Column(db.Float)  # in seconds

    def __init__(
        self,
        project_id,
        base_version: str,
        file: str,
        size: int,
        target_version: str,
        action: str,
        diff_path: str,
    ):
        self.project_id = project_id
        self.base_version = base_version
        self.file_name = file
        self.file_size = size
        self.target_version = target_version
        self.action = action

        if os.path.exists(diff_path):
            self.diff_size = os.path.getsize(diff_path)
            self.changes = GeoDiff().changes_count(diff_path)


class ProjectUser(db.Model):
    """Association table for project membership"""

    __tablename__ = "project_member"

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role = db.Column(
        ENUM(
            *[member.value for member in ProjectRole.__members__.values()],
            name="project_role",
        ),
        nullable=False,
    )
    project = db.relationship("Project", back_populates="project_users")
    user = db.relationship("User")
