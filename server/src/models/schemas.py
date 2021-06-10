# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.
import copy
import os
import re
from datetime import datetime
from marshmallow import fields, pre_dump, post_dump
from flask_login import current_user
from flask import current_app

from ..auth.schemas import UserSchema
from .. import ma
from ..mergin_utils import resolve_tags
from ..permissions import ProjectPermissions
from .db_models import Project, ProjectVersion, ProjectTransfer, Namespace, Account, AccessRequest, RemovedProject
from ..auth.models import User


class DateTimeWithZ(fields.DateTime):
    def __init__(self, **kwargs):
        super(DateTimeWithZ, self).__init__('%Y-%m-%dT%H:%M:%S%zZ', **kwargs)


class ProjectAccessSchema(ma.ModelSchema):
    owners = fields.List(fields.Integer())
    writers = fields.List(fields.Integer())
    readers = fields.List(fields.Integer())
    public = fields.Boolean()

    @post_dump
    def insert_usernames(self, data, **kwargs):
        """ Convert list of user ids in access levels to corresponding usernames
        Adds fields 'ownersnames', 'writersnames' and 'readersnames' to serialized data
        """
        if 'users_map' in self.context:
            # user map can be pass as context to save db query
            users_map = self.context['users_map']
        else:
            user_ids = data['owners'] + data['writers'] + data['readers']
            users_map = {u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()}

        for field in ('owners', 'writers', 'readers'):
            new_key = field + 'names'
            data[new_key] = []
            users_ids = data[field]
            for uid in users_ids:
                if uid not in users_map:
                    continue
                username = users_map[uid]
                data[new_key].append(username)
        return data


def project_user_permissions(project):
    return {
        "upload": ProjectPermissions.Upload.check(project, current_user),
        "update": ProjectPermissions.Update.check(project, current_user),
        "delete": ProjectPermissions.Delete.check(project, current_user)
    }

class FileInfoSchema(ma.ModelSchema):
    path = fields.String()
    size = fields.Integer()
    checksum = fields.String()
    location = fields.String(load_only=True)
    mtime = fields.String()
    diff = fields.Nested('self', required=False, missing={})
    history = fields.Dict(required=False, dump_only=True, missing={})

    @pre_dump
    def patch_history_field(self, data, **kwargs):
        """
        Append expiration to materialized versioned files and remove internal server metadata from final response.
        This is because history is general dict with yet unknown structure.
        #TODO resolve once marshmallow 3.0 is released.
        history = fields.Dict(keys=fields.String(), values=fields.Nested('self', exclude=['location', 'chunks']))
        """
        # diff field (self-nested does not contain history)
        if 'history' not in data:
            return data

        _data = copy.deepcopy(data)  # create deep copy to avoid messing around with original object
        for item in _data['history'].values():
            if 'diff' in item:
                item['diff'].pop('location', None)
                item['diff'].pop('sanitized_path', None)
                if self.context and 'project_dir' in self.context:
                    abs_path = os.path.join(self.context['project_dir'], item['location'])
                    if os.path.exists(abs_path):
                        expiration = os.path.getmtime(abs_path) + current_app.config['FILE_EXPIRATION']
                        item.update(expiration=datetime.utcfromtimestamp(expiration))
            item.pop('location', None)
            item.pop('chunks', None)
            item.pop('sanitized_path', None)
        return _data


class ProjectSchemaForVersion(ma.ModelSchema):
    """ Equivalent of ProjectSchema when version object is serialized """
    id = fields.UUID()
    created = DateTimeWithZ(attribute="project.created")
    creator = fields.Int(attribute="project.creator_id")
    uploads = fields.Function(lambda obj: obj.project.uploads.all())
    name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.namespace)
    access = fields.Method("_access")
    permissions = fields.Method("_permissions")
    disk_usage = fields.Method("_disk_usage")
    files = fields.Nested(FileInfoSchema(), many=True)
    tags = fields.Method("_tags")
    updated = DateTimeWithZ(attribute="created")
    version = fields.Function(lambda obj: obj.name)

    def _access(self, obj):
        return ProjectAccessSchema().dump(obj.project.access)

    def _permissions(self, obj):
        return project_user_permissions(obj.project)

    def _disk_usage(self, obj):
        return sum(f["size"] for f in obj.files)

    def _tags(self, obj):
        return resolve_tags(obj.files)


class ProjectAccessRequestSchema(ma.ModelSchema):
    user = fields.Nested(UserSchema(), exclude=['profile', 'is_admin', 'email', 'id', 'is_admin', 'verified_email'])
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Str()
    expire = DateTimeWithZ()

    class Meta:
        model = AccessRequest


class ProjectSchema(ma.ModelSchema):
    id = fields.UUID()
    files = fields.Nested(FileInfoSchema(), many=True)
    access = fields.Nested(ProjectAccessSchema())
    access_requests = fields.Nested(ProjectAccessRequestSchema(), many=True, exclude=['project'])
    permissions = fields.Function(project_user_permissions)
    version = fields.String(attribute='latest_version')
    namespace = fields.Str()
    created = DateTimeWithZ()

    class Meta:
        model = Project
        exclude = ['versions', 'transfers', 'latest_version', 'storage_params']


class ProjectListSchema(ma.ModelSchema):
    id = fields.UUID()
    name = fields.Str()
    namespace = fields.Str()
    access = fields.Nested(ProjectAccessSchema())
    permissions = fields.Function(project_user_permissions)
    version = fields.String(attribute='latest_version')
    updated = fields.Method("get_updated")
    created = DateTimeWithZ()
    creator = fields.Integer(attribute='creator_id')
    disk_usage = fields.Integer()
    tags = fields.List(fields.Str())
    has_conflict = fields.Method("get_has_conflict")


    def get_updated(self, obj):
        return obj.updated if obj.updated else obj.created


    def get_has_conflict(self, obj):
        # check if there is any conflict file in project
        files = obj.files
        for file in [f for f in files if '_conflict' in f.get('path')]:
            if len([f for f in files if f.get('path') == re.sub(r"(\.gpkg)(.*conflict.*)", r"\1", file.get('path'))]):
                return True
        return False


class ProjectVersionSchema(ma.ModelSchema):
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.namespace)
    author = fields.String()
    project = fields.Nested(ProjectSchema())
    changesets = fields.Method("get_diff_summary")
    files = fields.String()
    created = DateTimeWithZ()

    def get_diff_summary(self, obj):
        return obj.diff_summary()

    class Meta:
        model = ProjectVersion
        exclude = ['id', 'ip_address', 'ip_geolocation_country']


class NamespaceSchema(ma.ModelSchema):
    type = fields.Method("namespace_type")

    class Meta:
        model = Namespace
        fields = ('name', 'type')

    def namespace_type(self, obj):
        return obj.account.type


class ProjectTransferSchema(ma.ModelSchema):
    requested_by = fields.Method("requested_by_username")
    project = fields.Nested(ProjectSchema())
    project_name = fields.Function(lambda obj: obj.project.name)

    class Meta:
        model = ProjectTransfer
        fields = ('id', 'project_name', 'from_ns_name', 'to_ns_name', 'requested_by', 'requested_at', 'project', 'expire')

    def requested_by_username(self, obj):
        return obj.user.username


class AccountSchema(ma.ModelSchema):
    name = fields.Method('get_owner_name')
    email = fields.Method('get_owner_email')

    def get_owner_name(self, obj):
        return obj.name()

    def get_owner_email(self, obj):
        return obj.email()

    class Meta:
        model = Account
        fields = ('id', 'type', 'owner_id', 'name', 'email', )


class AccountExtendedSchema(ma.ModelSchema):
    id = fields.Integer()
    name = fields.String()
    type = fields.String()
    active = fields.Boolean()
    storage = fields.Integer()


class FullVersionSchema(ma.ModelSchema):
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.namespace)

    class Meta:
        model = ProjectVersion
        exclude = ['id']


class ProjectSchemaForDelete(ma.ModelSchema):
    versions = fields.Nested(FullVersionSchema(), many=True)
    creator_id = fields.Method("_creator_id")

    def _creator_id(self, obj):
        return obj.creator_id

    class Meta:
        model = Project
        exclude = ['transfers', 'uploads', 'access_requests', 'access']  # these fields will be lost


class RemovedProjectSchema(ma.ModelSchema):
    class Meta:
        model = RemovedProject
