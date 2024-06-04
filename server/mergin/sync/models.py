# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, asdict

from blinker import signal
from flask_login import current_user
from pygeodiff import GeoDiff
from sqlalchemy import text, null
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, UUID, JSONB, ENUM
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.types import String
from sqlalchemy.ext.hybrid import hybrid_property
from collections import OrderedDict
from pygeodiff.geodifflib import GeoDiffLibError
from flask import current_app

from .. import db
from .storages import DiskStorage
from .utils import int_version, is_versioned_file

Storages = {"local": DiskStorage}
project_deleted = signal("project_deleted")


class Project(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, index=True)
    storage_params = db.Column(db.JSON)
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    # metadata for project files (see also FileInfoSchema)
    files = db.deferred(db.Column(JSONB, default=[]))
    tags = db.Column(ARRAY(String), server_default="{}")
    disk_usage = db.Column(BIGINT, nullable=False, default=0)
    latest_version = db.Column(db.String, index=True)
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
        self.latest_version = "v0"

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

    def file_history(self, file, since, to, diffable=False):
        """
        Look up in project versions for history of versioned file.
        Returns ordered (from latest) dict with versions where some change happened and corresponding metadata.

        :Example:

        >>> self.file_history('mergin/base.gpkg', 'v1', 'v2')
        {'v2': {'checksum': '08b0e8caddafe74bf5c11a45f65cedf974210fed', 'location': 'v2/base.gpkg', 'path': 'base.gpkg',
        'size': 2793, 'change': 'updated'}, 'v1': {checksum': '89469a6482267de394c7c7270cb7ffafe694ea76',
        'location': 'v1/base.gpkg', 'mtime': '2019-07-18T07:52:38.770113Z', 'path': 'base.gpkg', 'size': 98304,
        'change': 'added'}}

        :param file: file path
        :type file: str
        :param since: start version for history (e.g. v1)
        :type since: str
        :param to: end version for history (e.g. v2)
        :type to: str
        :param diffable: whether to find only diffable history, defaults to False
        :type diffable: bool
        :returns: changes metadata for versions where some file change happened
        :rtype: dict
        """
        if not (is_versioned_file(file) and since is not None and to is not None):
            return {}

        history = OrderedDict()
        # query only those versions where file appeared in changes
        # we need to filter by timestamp instead of version name to be more effective
        sql = text(
            f"""
            WITH since_ts AS (
            SELECT COALESCE(
               (SELECT created FROM project_version
                WHERE project_id = :project_id
                AND name = :since),
                (SELECT NOW())
                ) AS value
            ),
            to_ts AS (
            SELECT COALESCE(
               (SELECT created FROM project_version
                WHERE project_id = :project_id
                AND name = :to),
                (SELECT NOW())
                ) AS value
            )
            SELECT expanded.name, expanded.change, expanded.files as value FROM
            (SELECT
                pv.name, pv.created, changes.key AS change, jsonb_array_elements(changes.value) AS files
             FROM project_version pv, jsonb_each(pv.changes) AS changes
             WHERE pv.changes @@ :json_changes_query
             AND pv.project_id = :project_id
             AND pv.created >= (SELECT value FROM since_ts)
             AND pv.created <= (SELECT value FROM to_ts)
            ) AS expanded
             WHERE expanded.files @> :json_file_query
             ORDER BY expanded.created DESC
        """
        )

        # in query we need exact format including correct quotes for search in jsonb
        # but because of sqlalchemy params formatting issues we construct json clauses manually
        json_changes_query = '$.*.path == "' + file + '"'
        json_file_query = '{"path": "' + file + '"}'
        params = {
            "project_id": self.id,
            "json_file_query": json_file_query,
            "json_changes_query": json_changes_query,
            "since": since,
            "to": to,
        }
        result = db.session.execute(sql, params).fetchall()
        for r in result:
            # example of custom query result
            # ('v1', 'added', {'checksum': '89469a6482267de394c7c7270cb7ffafe694ea76', 'location': 'v1/data/tests.gpkg',
            # 'mtime': '2019-07-18T07:52:38.770113Z', 'path': 'base.gpkg', 'size': 98304})

            # make sure we have "location" in response (e.g. 'added' changes do not have it stored)
            # which consists of version and file path
            if "location" not in r.value:
                r.value["location"] = os.path.join(r.name, r.value["path"])

            history[r.name] = {**r.value, "change": r.change}
            # end of file history
            if r.change in ["added", "removed"]:
                break

            # if we are interested only in 'diffable' history (not broken with forced update)
            if diffable and r.change == "updated" and "diff" not in r.value:
                break

        return history

    def sync_failed(self, client, error_type, error_details, user_id):
        """Commit failed attempt to sync failure history table"""
        new_failure = SyncFailuresHistory(
            self, client, error_type, error_details, user_id
        )
        db.session.add(new_failure)
        db.session.commit()

    def file_diffs_chain(self, file, version):
        """Find chain of diffs from the closest basefile that leads to a given file at certain project version.

        Returns basefile and list of diffs for gpkg that needs to be applied to reconstruct file.
        List of diffs can be empty if basefile was eventually asked. Basefile can be empty if file cannot be
        reconstructed (removed/renamed).

        :Example:

        >>> self.file_diffs_chain('mergin/base.gpkg', 'v3')
        {'checksum': '89469a6482267de394c7c7270cb7ffafe694ea76', 'location': 'v3/base.gpkg', 'path': 'base.gpkg', 'size': 98304, 'change': 'added', 'version': 'v3'},
        [{'checksum': '3749188af2721c60a0a6ac77935cd445934462d3', 'location': 'v4/base.gpkg-diff-aa78054c-6e43-4cbf-a7a9-cbbd3d84a0d5', 'path': 'base.gpkg-diff-aa78054c-6e43-4cbf-a7a9-cbbd3d84a0d5', 'size': 80}]

        :param file: file path
        :type file: str
        :param version: start version for history (e.g. v1)
        :type version: str
        :returns: basefile metadata, list of diffs metadata
        :rtype: dict, List[dict]
        """
        diffs = []
        base_meta = {}
        v_x = version  # the version of interest
        v_last = self.latest_version

        # we ask for the latest version which is always a basefile if the file has not been removed
        if v_x == v_last:
            f_meta = next((f for f in self.files if file == f["path"]), None)
            if f_meta:
                base_meta = f_meta
                base_meta["version"] = f_meta["location"].split(os.path.sep)[
                    0
                ]  # take actual version where file exists
            return base_meta, diffs

        # check if it would not be faster to look up from the latest version
        backward = (int_version(v_last) - int_version(v_x)) < int_version(v_x)

        if backward:
            # get ordered dict of file history starting with the latest version (v_last, ..., v_x+n, (..., v_x))
            history = self.file_history(file, v_x, v_last, diffable=True)
            if history:
                history_end = next(reversed(history))
                meta = history[history_end]
                # we have either full history of changes or v_x = v_x+n => no basefile in way, it is 'diffable' from the end
                if "diff" in meta:
                    # omit diff for target version as it would lead to previous version if reconstructed backward
                    diffs = [
                        value["diff"]
                        for key, value in reversed(history.items())
                        if key != v_x
                    ]
                    base_meta = history[next(iter(history))]
                    base_meta["version"] = next(iter(history))
                    return base_meta, diffs
                # there was either breaking change or v_x is a basefile itself
                else:
                    # we asked for basefile
                    if v_x == history_end and meta["change"] in ["added", "updated"]:
                        base_meta = meta
                        base_meta["version"] = v_x
                        diffs = []
                        return base_meta, diffs
                    # file was removed (or renamed for backward compatibility)
                    elif v_x == history_end:
                        return base_meta, diffs
                    # there was a breaking change in v_x+n, and we need to search from start
                    else:
                        pass

        # we haven't found something so far, search from v1
        if not (base_meta and diffs):
            # get ordered dict of file history starting with version of interest (v_x, ..., v_x-n, (..., v_1))
            history = self.file_history(file, "v1", v_x, diffable=True)
            if history:
                history_end = next(reversed(history))
                meta = history[history_end]
                # we found basefile
                if meta["change"] in ["added", "updated"]:
                    base_meta = meta
                    base_meta["version"] = history_end
                    if v_x == history_end:
                        diffs = []  # we asked for basefile
                    else:
                        diffs = [
                            value["diff"]
                            for value in list(reversed(history.values()))[
                                1:
                            ]  # basefile has no diff
                        ]
                # file was removed (or renamed for backward compatibility)
                else:
                    pass

        return base_meta, diffs

    def get_latest_version(self):
        """Return ProjectVersion object for the latest project version"""
        return ProjectVersion.query.filter_by(
            project_id=self.id, name=self.latest_version
        ).first()

    def next_version(self):
        """Next project version in vx format"""
        ver = int(self.latest_version.replace("v", "")) + 1
        return "v" + str(ver)

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
        - remove associated files and project versions
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
        self.files = null()
        pv_table = ProjectVersion.__table__
        db.session.execute(pv_table.delete().where(pv_table.c.project_id == self.id))
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
    project_permission: ProjectRole
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


class ProjectVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, index=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author = db.Column(db.String, index=True)
    # metadata with files changes
    # {"added": [{"checksum": "c9a4fd2afd513a97aba19d450396a4c9df8b2ba4", "path": "tests.qgs", "size": 31980}],
    # "removed": [], "renamed": [], "updated": []}
    changes = db.Column(JSONB)
    # metadata (see also FileInfoSchema) for files in actual version
    files = db.Column(JSONB)
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
    __table_args__ = (db.UniqueConstraint("project_id", "name"),)

    def __init__(
        self, project, name, author, changes, files, ip, user_agent=None, device_id=None
    ):
        self.project_id = project.id
        self.name = name
        self.author = author
        self.changes = changes
        self.files = files
        self.user_agent = user_agent
        self.ip_address = ip
        self.device_id = device_id
        self.project_size = sum(f["size"] for f in self.files) if self.files else 0
        # clean up changes metadata from chunks upload info
        for change in self.changes["updated"] + self.changes["added"]:
            change.pop("chunks", None)
            if "diff" in change:
                change["diff"].pop("chunks", None)

    @property
    def int_name(self) -> int:
        """Parsed version name as integer (v5 -> 5)"""
        return int(self.name.replace("v", ""))

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
        for f in self.changes["updated"]:
            if "diff" not in f:
                continue
            json_file = os.path.join(
                self.project.storage.project_dir, f["location"] + "-diff-summary"
            )
            changeset = os.path.join(
                self.project.storage.project_dir, f["diff"]["location"]
            )
            if not os.path.exists(json_file):
                try:
                    self.project.storage.geodiff.list_changes_summary(
                        changeset, json_file
                    )
                except GeoDiffLibError:
                    output[f["path"]] = {
                        "error": self.project.storage.gediff_log.getvalue(),
                        "size": f["diff"]["size"],
                    }
                    continue
            with open(json_file, "r") as jf:
                content = json.load(jf)
                if "geodiff_summary" not in content:
                    continue

                output[f["path"]] = {
                    "summary": content["geodiff_summary"],
                    "size": f["diff"]["size"],
                }

        return output


class Upload(db.Model):
    id = db.Column(db.String, primary_key=True)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
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

    def __init__(self, project, version, changes, user_id):
        self.id = str(uuid.uuid4())
        self.project_id = project.id
        self.version = version
        self.changes = changes
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
        self.last_version = project.latest_version
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

    def __init__(self, project_id, base_meta, target_version, action, diff_path):
        self.project_id = project_id
        self.base_version = base_meta["version"]
        self.file_name = base_meta["path"]
        self.file_size = base_meta["size"]
        self.target_version = target_version
        self.action = action

        if os.path.exists:
            self.diff_size = os.path.getsize(diff_path)
            self.changes = GeoDiff().changes_count(diff_path)
