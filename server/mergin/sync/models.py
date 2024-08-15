# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Set, Tuple
from dataclasses import dataclass, asdict

from blinker import signal
from flask_login import current_user
from pygeodiff import GeoDiff
from sqlalchemy import text, null, desc, nullslast
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, UUID, JSONB, ENUM
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.types import String
from sqlalchemy.ext.hybrid import hybrid_property
from pygeodiff.geodifflib import GeoDiffLibError
from flask import current_app

from .files import (
    File,
    UploadFile,
    UploadChanges,
    ChangesSchema,
    ProjectFile,
)
from .. import db
from .storages import DiskStorage
from .utils import is_versioned_file, is_qgis

Storages = {"local": DiskStorage}
project_deleted = signal("project_deleted")


class PushChangeType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UPDATE_DIFF = "update_diff"

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]


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

    creator = db.relationship(
        "User", uselist=False, backref=db.backref("projects"), foreign_keys=[creator_id]
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
        """Get project files from changes (FileHistory) and saved them for later use"""
        if self.latest_version is None:
            return

        query = f"""
            WITH latest_changes AS (
                SELECT
                    fp.id,
                    fp.project_id,
                    max(pv.name) AS version
                FROM
                    project_version pv
                    LEFT OUTER JOIN file_history fh ON fh.version_id = pv.id
                    LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
                WHERE
                    pv.project_id = :project_id
                    AND pv.name <= :latest_version
                GROUP BY
                    fp.id, fp.project_id
            ), aggregates AS (
                SELECT
                    project_id,
                    array_agg(fh.id) AS files_ids
                FROM latest_changes ch
                LEFT OUTER JOIN file_history fh ON (fh.file_path_id = ch.id AND fh.project_version_name = ch.version)
                WHERE fh.change != 'delete'
                GROUP BY project_id
            )
            UPDATE latest_project_files pf
            SET file_history_ids = a.files_ids
            FROM aggregates a
            WHERE a.project_id = pf.project_id;
        """
        params = {"project_id": self.id, "latest_version": self.latest_version}
        db.session.execute(query, params)
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
                fh.diff,
                fh.location,
                fh.checksum,
                pv.created AS mtime
            FROM files_ids
            LEFT OUTER JOIN file_history fh ON fh.id = files_ids.fh_id
            LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
            LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id;
        """
        params = {"project_id": self.id}
        files = [
            ProjectFile(
                path=row.path,
                size=row.size,
                checksum=row.checksum,
                location=row.location,
                mtime=row.mtime,
                diff=File(**row.diff) if row.diff else None,
            )
            for row in db.session.execute(query, params).fetchall()
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
        - remove associated files and their history and project versions
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
        pv_table = ProjectVersion.__table__
        # remove versions and file history items with cascade
        db.session.execute(pv_table.delete().where(pv_table.c.project_id == self.id))
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
        self.access.owners = self.access.writers = self.access.editors = (
            self.access.readers
        ) = []
        access_requests = (
            AccessRequest.query.filter_by(project_id=self.id)
            .filter(AccessRequest.status.is_(None))
            .all()
        )
        for req in access_requests:
            req.resolve(status=RequestStatus.DECLINED, resolved_by=self.removed_by)
        db.session.commit()
        project_deleted.send(self)


class ProjectRole(Enum):
    OWNER = "owner"
    WRITER = "writer"
    EDITOR = "editor"
    READER = "reader"

    def __gt__(self, other):
        """
        Compare project roles

        https://docs.python.org/3/library/enum.html#enum.EnumType.__members__
        """
        members = list(ProjectRole.__members__)
        if members.index(self.name) < members.index(other.name):
            return True
        else:
            return False


@dataclass
class ProjectAccessDetail:
    id: int or str
    email: str
    role: str
    username: str
    name: Optional[str]
    project_permission: str
    type: str


class ProjectAccess(db.Model):
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    public = db.Column(db.Boolean, default=False, index=True)
    owners = db.Column(ARRAY(db.Integer), server_default="{}")
    readers = db.Column(ARRAY(db.Integer), server_default="{}")
    writers = db.Column(ARRAY(db.Integer), server_default="{}")
    editors = db.Column(ARRAY(db.Integer), server_default="{}")

    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref(
            "access",
            single_parent=True,
            uselist=False,
            cascade="all,delete",
            lazy="joined",
        ),
    )

    __table_args__ = (
        db.Index("ix_project_access_owners", owners, postgresql_using="gin"),
        db.Index("ix_project_access_readers", readers, postgresql_using="gin"),
        db.Index("ix_project_access_writers", writers, postgresql_using="gin"),
        db.Index("ix_project_access_editors", editors, postgresql_using="gin"),
    )

    def __init__(self, project, public=False):
        self.project = project
        self.owners = [project.creator.id]
        self.writers = [project.creator.id]
        self.readers = [project.creator.id]
        self.editors = [project.creator.id]
        self.project_id = project.id
        self.public = public

    def get_role(self, user_id: int) -> Optional[ProjectRole]:
        """Get user role based on mapping to DB ACL"""
        if user_id in self.owners:
            return ProjectRole.OWNER
        elif user_id in self.writers:
            return ProjectRole.WRITER
        elif user_id in self.editors:
            return ProjectRole.EDITOR
        elif user_id in self.readers:
            return ProjectRole.READER
        else:
            return None

    @staticmethod
    def _permission_attrs(role: ProjectRole) -> List[str]:
        """Return db attributes list related to permission"""
        # because roles do not inherit, they must be un/set explicitly in db ACLs
        perm_list = {
            ProjectRole.READER: ["readers"],
            ProjectRole.EDITOR: ["editors", "readers"],
            ProjectRole.WRITER: ["writers", "editors", "readers"],
            ProjectRole.OWNER: ["owners", "writers", "editors", "readers"],
        }
        return perm_list[role]

    def set_role(self, user_id: int, role: ProjectRole) -> None:
        """Set user role"""
        self.unset_role(user_id)
        for attr in self._permission_attrs(role):
            ids = getattr(self, attr)
            if user_id not in ids:
                ids.append(user_id)
                setattr(self, attr, ids)
                flag_modified(self, attr)

    def unset_role(self, user_id: int) -> None:
        """Remove user's role"""
        role = self.get_role(user_id)
        if not role:
            return

        for attr in self._permission_attrs(role):
            ids = getattr(self, attr)
            if user_id in ids:
                ids.remove(user_id)
                setattr(self, attr, ids)
                flag_modified(self, attr)

    def bulk_update(self, new_access: Dict) -> Set[int]:
        """From new access lists do bulk update and return ids with any change applied"""
        diff = set()
        for key in ("owners", "writers", "editors", "readers"):
            new_value = new_access.get(key, None)
            if not new_value:
                continue
            old_value = set(getattr(self, key))
            diff = diff.union(set(new_value).symmetric_difference(old_value))
            setattr(self, key, list(new_value))

        # make sure lists are consistent (they inherit from each other)
        self.writers = list(set(self.writers).union(set(self.owners)))
        self.editors = list(set(self.editors).union(set(self.writers)))
        self.readers = list(set(self.readers).union(set(self.editors)))
        return diff


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

    def __init__(self, project_id, path):
        self.project_id = project_id
        self.path = path


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
    diff = db.Column(JSONB)
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
    ):
        self.file = file
        self.size = size
        self.checksum = checksum
        self.location = location
        self.diff = diff
        self.change = change.value

    @property
    def path(self) -> str:
        return self.file.path

    @property
    def diff_file(self) -> Optional[File]:
        if self.diff:
            return File(**self.diff)

    @property
    def mtime(self) -> datetime:
        return self.version.created

    @property
    def abs_path(self) -> str:
        return os.path.join(self.version.project.storage.project_dir, self.location)

    @property
    def expiration(self) -> Optional[datetime]:
        if not self.diff:
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
            .join(FileHistory.version)
            .filter(
                ProjectVersion.project_id == project_id,
                ProjectVersion.name <= to,
                ProjectVersion.name >= since,
                ProjectFilePath.path == file,
            )
            .order_by(desc(ProjectVersion.created))
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
            if (
                diffable
                and item.change == PushChangeType.UPDATE.value
                and not item.diff
            ):
                break

        return history

    @classmethod
    def diffs_chain(
        cls, project: Project, file: str, version: int
    ) -> Tuple[Optional[FileHistory], List[Optional[File]]]:
        """Find chain of diffs from the closest basefile that leads to a given file at certain project version.

        Returns basefile and list of diffs for gpkg that needs to be applied to reconstruct file.
        List of diffs can be empty if basefile was eventually asked. Basefile can be empty if file cannot be
        reconstructed (removed/renamed).
        """
        diffs = []
        basefile = None
        v_x = version  # the version of interest
        v_last = project.latest_version

        # we ask for the latest version which is always a basefile if the file has not been removed
        if v_x == v_last:
            latest_change = (
                FileHistory.query.join(ProjectFilePath)
                .join(FileHistory.version)
                .filter(
                    ProjectFilePath.path == file,
                    ProjectVersion.project_id == project.id,
                )
                .order_by(desc(ProjectVersion.created))
                .first()
            )
            if latest_change.change != PushChangeType.DELETE.value:
                return latest_change, []
            else:
                # file is actually not in the latest project version
                return None, []

        # check if it would not be faster to look up from the latest version
        backward = (v_last - v_x) < v_x

        if backward:
            # get list of file history changes starting with the latest version (v_last, ..., v_x+n, (..., v_x))
            history = FileHistory.changes(project.id, file, v_x, v_last, diffable=True)
            if history:
                first_change = history[-1]
                # we have either full history of changes or v_x = v_x+n => no basefile in way, it is 'diffable' from the end
                if first_change.diff:
                    # omit diff for target version as it would lead to previous version if reconstructed backward
                    diffs = [
                        value.diff_file
                        for value in reversed(history)
                        if value.version.name != v_x
                    ]
                    basefile = history[0]
                    return basefile, diffs
                # there was either breaking change or v_x is a basefile itself
                else:
                    # we asked for basefile
                    if v_x == first_change.version.name and first_change.change in [
                        PushChangeType.CREATE.value,
                        PushChangeType.UPDATE.value,
                    ]:
                        return first_change, []
                    # file was removed (or renamed for backward compatibility)
                    elif v_x == first_change.version.name:
                        return basefile, diffs
                    # there was a breaking change in v_x+n, and we need to search from start
                    else:
                        pass

        # we haven't found anything so far, search from v1
        if not (basefile and diffs):
            # get ordered dict of file history starting with version of interest (v_x, ..., v_x-n, (..., v_1))
            history = FileHistory.changes(project.id, file, 1, v_x, diffable=True)
            if history:
                first_change = history[-1]
                # we found basefile
                if first_change.change in [
                    PushChangeType.CREATE.value,
                    PushChangeType.UPDATE.value,
                ]:
                    basefile = first_change
                    if v_x == first_change.version.name:
                        # we asked for basefile
                        diffs = []
                    else:
                        # basefile has no diff
                        diffs = [
                            value.diff_file for value in list(reversed(history))[1:]
                        ]
                # file was removed (or renamed for backward compatibility)
                else:
                    pass

        return basefile, diffs


class ProjectVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Integer, index=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author = db.Column(db.String, index=True)
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
        author: str,
        changes: UploadChanges,
        ip: str,
        user_agent: str = None,
        device_id: str = None,
    ):
        self.project = project
        self.project_id = project.id
        self.name = name
        self.author = author
        self.user_agent = user_agent
        self.ip_address = ip
        self.device_id = device_id

        latest_files_map = {
            fh.path: fh.id
            for fh in FileHistory.query.filter(
                FileHistory.id.in_(self.project.latest_project_files.file_history_ids)
            ).all()
        }

        changed_files_paths = [
            f.path for f in changes.updated + changes.removed + changes.added
        ]
        existing_files_map = {
            f.path: f
            for f in ProjectFilePath.query.filter_by(project_id=self.project_id)
            .filter(ProjectFilePath.path.in_(changed_files_paths))
            .all()
        }

        for key in (
            ("added", PushChangeType.CREATE),
            ("updated", PushChangeType.UPDATE),
            ("removed", PushChangeType.DELETE),
        ):
            change_attr = key[0]
            change_type = key[1]

            for upload_file in getattr(changes, change_attr):
                is_diff_change = (
                    change_type is PushChangeType.UPDATE
                    and upload_file.diff is not None
                )

                file = existing_files_map.get(
                    upload_file.path, ProjectFilePath(self.project_id, upload_file.path)
                )
                fh = FileHistory(
                    file=file,
                    size=upload_file.size,
                    checksum=upload_file.checksum,
                    location=upload_file.location,
                    diff=asdict(upload_file.diff) if upload_file.diff else null(),
                    change=(
                        PushChangeType.UPDATE_DIFF if is_diff_change else change_type
                    ),
                )
                fh.version = self
                fh.project_version_name = self.name
                db.session.add(fh)
                db.session.flush()

                if change_type is PushChangeType.DELETE:
                    latest_files_map.pop(fh.path, None)
                else:
                    latest_files_map[fh.path] = fh.id

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

    def _files_forward_search(self):
        """Calculate version files using lookup from the first version"""
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
                fh.diff,
                fh.location,
                fh.checksum,
                pv.created AS mtime
            FROM latest_changes ch
            LEFT OUTER JOIN file_history fh ON (fh.file_path_id = ch.id AND fh.project_version_name = ch.version)
            LEFT OUTER JOIN project_file_path fp ON fp.id = fh.file_path_id
            LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
            WHERE fh.change != 'delete';
        """
        params = {"project_id": self.project_id, "version": self.name}
        return db.session.execute(query, params).fetchall()

    def _files_backward_search(self):
        """Calculate version files using lookup from the last version"""
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
                fh.diff,
                fh.location,
                fh.checksum,
                pv.created AS mtime
            FROM files_changes_before_version ch
            INNER JOIN file_history fh ON (fh.file_path_id = ch.file_id AND fh.project_version_name = ch.version)
            INNER JOIN project_file_path fp ON fp.id = fh.file_path_id
            INNER JOIN project_version pv ON pv.id = fh.version_id
            WHERE fh.change != 'delete'
            ORDER BY fp.path;
        """
        params = {"project_id": self.project_id, "version": self.name}
        return db.session.execute(query, params).fetchall()

    @property
    def files(self) -> List[ProjectFile]:
        # return from cache
        if self.name == self.project.latest_version:
            return self.project.files

        if self.name < self.project.latest_version / 2:
            result = self._files_forward_search()
        else:
            result = self._files_backward_search()
        files = [
            ProjectFile(
                path=row.path,
                size=row.size,
                checksum=row.checksum,
                location=row.location,
                mtime=row.mtime,
                diff=File(**row.diff) if row.diff else None,
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
        result = db.session.execute(query, params).fetchall()
        return {row[0]: row[1] for row in result}


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

    def __init__(
        self, project: Project, version: int, changes: UploadChanges, user_id: int
    ):
        self.id = str(uuid.uuid4())
        self.project_id = project.id
        self.version = version
        self.changes = ChangesSchema().dump(changes)
        self.user_id = user_id


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
        project_access = self.project.access
        PERMISSION_PROJECT_ROLE = {
            "read": ProjectRole.READER,
            "edit": ProjectRole.EDITOR,
            "write": ProjectRole.WRITER,
            "owner": ProjectRole.OWNER,
        }

        project_access.set_role(
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
    error_details = db.Column(db.String, index=True)
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

        if os.path.exists:
            self.diff_size = os.path.getsize(diff_path)
            self.changes = GeoDiff().changes_count(diff_path)
