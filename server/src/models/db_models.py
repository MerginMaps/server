# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import json
import os
import uuid
from datetime import datetime, timedelta
from blinker import signal
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, ENUM, UUID
from sqlalchemy.types import String
from collections import OrderedDict
from pygeodiff.geodifflib import GeoDiffLibError

from .. import current_app, db
from ..storages import DiskStorage
from ..auth.models import User  # pylint: disable=W0611
from ..mergin_utils import int_version, is_versioned_file

Storages = {
    "local": DiskStorage
}

account_created = signal('account_created')
account_inactivated = signal('account_inactivated')


class Project(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, index=True)
    storage_params = db.Column(db.JSON)
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    # metadata for project files (see also FileInfoSchema)
    files = db.Column(db.JSON, default=[])
    tags = db.Column(ARRAY(String), server_default="{}")
    disk_usage = db.Column(BIGINT, nullable=False, default=0)
    latest_version = db.Column(db.String, index=True)

    creator = db.relationship("User", uselist=False, backref=db.backref("projects", cascade="all,delete"))
    namespace = db.Column(db.String, db.ForeignKey("namespace.name", ondelete="CASCADE"), index=True)
    __table_args__ = (db.UniqueConstraint('name', 'namespace'),)

    def __init__(self, name, storage_params, creator, namespace, **kwargs):  # pylint: disable=W0613
        self.name = name
        self.storage_params = storage_params
        self.creator = creator
        self.namespace = namespace
        self.latest_version = "v0"

    @property
    def storage(self):
        if not hasattr(self, '_storage'):  # best approach, seriously
            StorageBackend = Storages[self.storage_params['type']]
            self._storage = StorageBackend(self)  # pylint: disable=W0201
        return self._storage

    def file_history(self, file, since, to):
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
        :returns: changes metadata for versions where some file change happened
        :rtype: dict
        """
        since = int_version(since)
        to = int_version(to)
        if not (is_versioned_file(file) and since is not None and to is not None):
            return {}

        history = OrderedDict()
        versions = sorted(self.versions, key=lambda v: int_version(v.name))
        # version v0 was added as initial version later and some older projects may not have it
        if versions[0].name == "v0":
            to = to + 1
            since = since + 1

        for version in reversed(versions[since-1:to]):
            f_change = version.find_file_change(file)
            if not f_change:
                continue
            # make sure we find with correct filename next time
            if f_change['change'] == 'renamed':
                file = f_change['path']
            history[version.name] = f_change
            # end of file history
            if f_change['change'] in ['added', 'removed']:
                break

        return history


class ProjectAccess(db.Model):
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), primary_key=True, index=True)
    public = db.Column(db.Boolean, default=False, index=True)
    owners = db.Column(ARRAY(db.Integer), server_default="{}")
    readers = db.Column(ARRAY(db.Integer), server_default="{}")
    writers = db.Column(ARRAY(db.Integer), server_default="{}")

    project = db.relationship("Project",
                              uselist=False,
                              backref=db.backref("access", single_parent=True, uselist=False, cascade="all,delete", lazy='joined'))

    __table_args__ = (db.Index('ix_project_access_owners', owners, postgresql_using="gin"),
                      db.Index('ix_project_access_readers', readers, postgresql_using="gin"),
                      db.Index('ix_project_access_writers', writers, postgresql_using="gin"),)

    def __init__(self, project, public=False):
        self.project = project
        self.owners = [project.creator.id]
        self.writers = [project.creator.id]
        self.readers = [project.creator.id]
        self.project_id = project.id
        self.public = public


class ProjectVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, index=True)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author = db.Column(db.String, index=True)
    # metadata with files changes
    # {"added": [{"checksum": "c9a4fd2afd513a97aba19d450396a4c9df8b2ba4", "path": "test.qgs", "size": 31980}],
    # "removed": [], "renamed": [], "updated": []}
    changes = db.Column(db.JSON)
    # metadata (see also FileInfoSchema) for files in actual version
    files = db.Column(db.JSON)
    user_agent = db.Column(db.String, index=True)
    ip_address = db.Column(db.String, index=True)
    ip_geolocation_country = db.Column(db.String, index=True)  # geolocation country derived from IP (with celery job)
    project_size = db.Column(BIGINT, nullable=False, default=0, index=True)  # size of project at current version (incl. files from older versions)

    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref("versions", single_parent=True, lazy='subquery', cascade="all,delete", order_by="desc(ProjectVersion.created)")
    )

    def __init__(self, project, name, author, changes, files, ip, user_agent=None):
        self.project_id = project.id
        self.name = name
        self.author = author
        self.changes = changes
        self.files = files
        self.user_agent = user_agent
        self.ip_address = ip
        self.project_size = sum(f["size"] for f in self.files) if self.files else 0

    def find_file_change(self, file):
        """
        Browse version changes and return requested file change metadata (if any). Append type of change.

        :Example:

        >>> self.find_file_change('data/test.gpkg')
        {'checksum': '89469a6482267de394c7c7270cb7ffafe694ea76', 'location': 'v1/data/test.gpkg',
        'mtime': '2019-07-18T07:52:38.770113Z', 'path': 'base.gpkg', 'size': 98304, 'change': 'added'}

        :param file: file path
        :type file: str
        :returns: change metadata
        :rtype: dict
        """
        for k, v in self.changes.items():
            match_key = 'new_path' if k == 'renamed' else 'path'
            changed_item = next((item for item in v if item.get(match_key) == file), None)
            if changed_item:
                changed_item['change'] = k
                changed_item['location'] = next((f['location'] for f in self.files if f['path'] == changed_item[match_key]), None)
                # append location of diff file
                if 'diff' in changed_item:
                    changed_item['diff']['location'] = next(
                        (f['diff']['location'] for f in self.files if f['path'] == changed_item[match_key]), None)
                return changed_item

    def diff_summary(self):
        """ Calculate diff summary for versioned files updated with geodiff

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
        for f in self.changes["updated"]:
            if 'diff' not in f:
                continue
            json_file = os.path.join(self.project.storage.project_dir, f['location'] + '-diff-summary')
            changeset = os.path.join(self.project.storage.project_dir, f['diff']['location'])
            if not os.path.exists(json_file):
                try:
                    self.project.storage.geodiff.list_changes_summary(changeset, json_file)
                except GeoDiffLibError as e:
                    output[f['path']] = {
                        "error": str(e),
                        "size": f['diff']['size']
                    }
                    continue

            with open(json_file, 'r') as jf:
                content = json.load(jf)
                if 'geodiff_summary' not in content:
                    continue

                output[f['path']] = {
                    "summary": content["geodiff_summary"],
                    "size": f['diff']['size']
                }

        return output


class Namespace(db.Model):
    name = db.Column(db.String, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id", ondelete="CASCADE"))
    storage = db.Column(BIGINT, nullable=False, default=os.environ.get('DEFAULT_STORAGE_SIZE', 100 * 1024 * 1024))

    account = db.relationship("Account", uselist=False, backref=db.backref("namespace", single_parent=True, uselist=False, cascade="all,delete"))

    def __init__(self, name, account_id):
        self.name = name
        self.account_id = account_id

    def projects(self):
        return Project.query.filter_by(namespace=self.name).all()

    def owner(self):
        self.account.owner()

    def disk_usage(self):
        return sum(p.disk_usage for p in self.projects())


class Upload(db.Model):
    id = db.Column(db.String, primary_key=True)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True)
    version = db.Column(db.Integer, index=True)
    changes = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref("uploads", single_parent=True, lazy='dynamic', cascade="all,delete")
    )
    __table_args__ = (
        db.UniqueConstraint('project_id', 'version'),
    )

    def __init__(self, project, version, changes, user_id):
        self.id = str(uuid.uuid4())
        self.project_id = project.id
        self.version = version
        self.changes = changes
        self.user_id = user_id


class ProjectTransfer(db.Model):
    id = db.Column(db.String, primary_key=True)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True)
    from_ns_name = db.Column(db.String, nullable=False, index=True)  # cached value for easier lookups
    to_ns_name = db.Column(db.String, db.ForeignKey("namespace.name", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    expire = db.Column(db.DateTime)

    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref("transfers", single_parent=True, lazy='dynamic', cascade="all,delete")
    )
    to_ns = db.relationship(
        "Namespace",
        backref=db.backref("transfers", single_parent=True, lazy='dynamic', cascade="all,delete")
    )
    user = db.relationship("User")

    __table_args__ = (db.UniqueConstraint('project_id'),)

    class TransferError(Exception):
        def __init__(self, reason=None):
            error = 'Project transfer failed'
            if reason:
                error = '{} : {}'.format(error, reason)
            self.errors = error

    def __init__(self, project, to_namespace, requested_by):
        """ Initiate project transfer to different namespace

        :param project: project to be transferred
        :type project: Project

        :param to_namespace: the namespace for project to be transferred
        :type to_namespace: Namespace

        :param requested_by: requested by
        :type requested_by: User.id
        """
        self.id = str(uuid.uuid4())
        self.project_id = project.id
        self.from_ns_name = project.namespace
        self.to_ns_name = to_namespace.name
        self.requested_by = requested_by
        self.expire = datetime.utcnow() + timedelta(seconds=current_app.config['TRANSFER_EXPIRATION'])

        if to_namespace.name == project.namespace:
            raise self.TransferError('origin and destination namespaces are the same')

    def is_expired(self):
        """ Check if transfer request is expired
        :rtype: bool
        """
        return datetime.utcnow() > self.expire


class Account(db.Model):
    """ Reference class to claim service ownership either by user or organisation """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(ENUM("user", "organisation", name="account_type"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, nullable=False, index=True)

    def __init__(self, type, owner_id):
        self.type = type
        self.owner_id = owner_id

    def owner(self):
        from ..organisation.models import Organisation

        if self.type == 'organisation':
            return Organisation.query.get(self.owner_id)
        elif self.type == 'user':
            return User.query.get(self.owner_id)
        else:
            return

    def can_edit(self, user_id):
        from ..organisation.models import Organisation
        owner = self.owner()
        if isinstance(owner, User):
            return owner.id == user_id
        elif isinstance(owner, Organisation):
            return user_id in owner.owners
        else:
            return False

    def email(self):
        from ..organisation.models import Organisation
        owner = self.owner()

        if isinstance(owner, User):
            return owner.email
        elif isinstance(owner, Organisation):
            owner_id = owner.owners[0]
            user = User.query.get(owner_id)
            return user.email
        else:
            return ''

    def name(self):
        from ..organisation.models import Organisation

        owner = self.owner()
        if isinstance(owner, User):
            return owner.username
        elif isinstance(owner, Organisation):
            return owner.name
        else:
            return ''

    def created(self, connection=None):
        """ Emit blinker.signal event that account has been created """
        account_created.send(self, connection=connection)

    def inactivated(self, action):
        account_inactivated.send(self, action=action)


class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), index=True)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id", ondelete="CASCADE"), index=True)
    namespace = db.Column(db.String, nullable=False, index=True)  # cached value for easier lookups
    expire = db.Column(db.DateTime)

    user = db.relationship("User", uselist=False)

    project = db.relationship(
        "Project",
        uselist=False,
        backref=db.backref("access_requests", single_parent=True, cascade="all,delete")
    )

    def __init__(self, project, user_id):
        self.project_id = project.id
        self.namespace = project.namespace
        self.user_id = user_id
        self.expire = datetime.utcnow() + timedelta(seconds=current_app.config['PROJECT_ACCESS_REQUEST'])

    def accept(self, permissions):
        """ The accept to project access request
        """
        # user = User.query.filter(User.username == self.username)
        project_access = self.project.access
        readers = project_access.readers.copy()
        writers = project_access.writers.copy()
        owners = project_access.owners.copy()
        readers.append(self.user_id)
        project_access.readers = readers
        if permissions == "write" or permissions == "owner":
            writers.append(self.user_id)
            project_access.writers = writers
        if permissions == "owner":
            owners.append(self.user_id)
            project_access.owners = owners

        db.session.delete(self)
        db.session.commit()


class RemovedProject(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, index=True)
    namespace = db.Column(db.String, nullable=False, index=True)
    properties = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    removed_by = db.Column(db.String, nullable=False)

    def __init__(self, project, removed_by):
        from .schemas import ProjectSchemaForDelete

        self.name = project.name
        self.namespace = project.namespace
        self.properties = ProjectSchemaForDelete().dump(project)
        self.removed_by = removed_by
