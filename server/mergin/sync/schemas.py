# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import re
from marshmallow import fields, ValidationError, Schema, post_dump
from flask_login import current_user
from flask import current_app

from .. import ma
from .files import ProjectFileSchema, FileSchema
from .permissions import ProjectPermissions
from .models import Project, ProjectVersion, AccessRequest, FileHistory, PushChangeType
from ..app import DateTimeWithZ
from ..auth.models import User


class ProjectAccessSchema(ma.SQLAlchemyAutoSchema):
    owners = fields.List(fields.Integer())
    writers = fields.List(fields.Integer())
    editors = fields.List(fields.Integer())
    readers = fields.List(fields.Integer())
    public = fields.Boolean()

    @post_dump
    def insert_usernames(self, data, **kwargs):
        """Convert list of user ids in access levels to corresponding usernames
        Adds fields 'ownersnames', 'writersnames' and 'readersnames' to serialized data
        """
        if "users_map" in self.context:
            # user map can be pass as context to save db query
            users_map = self.context["users_map"]
        else:
            user_ids = (
                data["owners"] + data["writers"] + data["editors"] + data["readers"]
            )
            users_map = {
                u.id: u.username
                for u in User.query.filter(
                    User.id.in_(set(user_ids)), User.active
                ).all()
            }

        for field in ("owners", "writers", "editors", "readers"):
            new_key = field + "names"
            data[new_key] = []
            users_ids = data[field]
            for uid in users_ids:
                if uid not in users_map:
                    data[field].remove(uid)
                    continue
                username = users_map[uid]
                data[new_key].append(username)
        return data


def project_user_permissions(project):
    return {
        # This mapping (upload) is used by mobile and mergin client to check if it is possible to make push to server.
        # We can rename it in future upload -> Edit and add new Write key.
        "upload": ProjectPermissions.Edit.check(project, current_user),
        "update": ProjectPermissions.Update.check(project, current_user),
        "delete": ProjectPermissions.Delete.check(project, current_user),
    }


class FileHistorySchema(ma.SQLAlchemyAutoSchema):
    mtime = DateTimeWithZ()
    diff = fields.Nested(FileSchema(), attribute="diff_file", exclude=("location",))
    expiration = DateTimeWithZ(attribute="expiration", dump_only=True)

    class Meta:
        model = FileHistory
        load_instance = True
        fields = (
            "path",
            "size",
            "checksum",
            "mtime",
            "diff",
            "expiration",
            "change",
        )

    @post_dump
    def patch_field(self, data, **kwargs):
        # patch change type from internal type to public API value
        if data.get("change") == "create":
            data["change"] = "added"
        elif data.get("change") == "delete":
            data["change"] = "removed"
        elif data.get("change") in ("update", "update_diff"):
            data["change"] = "updated"

        # drop 'diff' key entirely if empty or None as clients would expect
        if not data.get("diff"):
            data.pop("diff")
        return data


class ProjectSchemaForVersion(ma.SQLAlchemyAutoSchema):
    """Equivalent of ProjectSchema when version object is serialized"""

    id = fields.UUID(attribute="project.id")
    created = DateTimeWithZ(attribute="project.created")
    creator = fields.Int(attribute="project.creator_id")
    uploads = fields.Method("_uploads")
    name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.workspace.name)
    access = fields.Method("_access")
    permissions = fields.Method("_permissions")
    disk_usage = fields.Method("_disk_usage")
    files = fields.Nested(ProjectFileSchema(), many=True)
    tags = fields.Method("_tags")
    updated = DateTimeWithZ(attribute="created")
    version = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.name))
    role = fields.Method("_role")

    def _role(self, obj):
        role = ProjectPermissions.get_user_project_role(obj.project, current_user)
        if not role:
            return None
        return role.value

    def _uploads(self, obj):
        return [u.id for u in obj.project.uploads.all()]

    def _access(self, obj):
        return ProjectAccessSchema().dump(obj.project.access)

    def _permissions(self, obj):
        return project_user_permissions(obj.project)

    def _disk_usage(self, obj):
        return sum(f.size for f in obj.files)

    def _tags(self, obj):
        return obj.resolve_tags()


class ProjectAccessRequestSchema(ma.SQLAlchemyAutoSchema):
    requested_by = fields.Method("_requested_by")
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.workspace.name)
    expire = DateTimeWithZ()

    def _requested_by(self, obj):
        u = User.query.get(obj.requested_by)
        return u.username if u else ""

    class Meta:
        model = AccessRequest
        load_instance = True
        exclude = ("resolved_by", "resolved_at", "status", "requested_at")


class ProjectSchema(ma.SQLAlchemyAutoSchema):
    id = fields.UUID()
    files = fields.Nested(ProjectFileSchema(), many=True)
    access = fields.Nested(ProjectAccessSchema())
    permissions = fields.Function(project_user_permissions)
    version = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.latest_version))
    namespace = fields.Function(lambda obj: obj.workspace.name)
    created = DateTimeWithZ()
    updated = DateTimeWithZ()
    creator = fields.Integer(attribute="creator_id")
    uploads = fields.Method("_uploads")
    role = fields.Method("_role")

    def _role(self, obj):
        role = ProjectPermissions.get_user_project_role(obj, current_user)
        if not role:
            return None
        return role.value

    def _uploads(self, obj):
        return [u.id for u in obj.uploads.all()]

    class Meta:
        model = Project
        exclude = ["latest_version", "storage_params"]
        load_instance = True


class ProjectListSchema(ma.SQLAlchemyAutoSchema):
    id = fields.UUID()
    name = fields.Str()
    namespace = fields.Method("get_workspace_name")
    access = fields.Nested(ProjectAccessSchema())
    permissions = fields.Function(project_user_permissions)
    version = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.latest_version))
    updated = fields.Method("get_updated")
    created = DateTimeWithZ()
    creator = fields.Integer(attribute="creator_id")
    disk_usage = fields.Integer()
    tags = fields.List(fields.Str())
    has_conflict = fields.Method("get_has_conflict")

    def get_updated(self, obj):
        return obj.updated if obj.updated else obj.created

    def get_has_conflict(self, obj):
        """Check if there is any conflict file in project generated by client
        Patterns to check:
        - file.[gpkg|qgs|qgz]_conflict_copy (older convention)
        - file.gpkg_rebase_conflicts (older convention)
        - file (conflicted copy, user vx).*
        - file (edit conflict, user vx).json
        """
        regex = r"(\.gpkg|\.qgs|.qgz)(.*conflict.*)|( \(.*conflict.*)"
        return any(re.search(regex, file.path) for file in obj.files)

    def get_workspace_name(self, obj):
        """Discover ProjectListSchema workspace name"""
        try:
            workspaces_map = self.context["workspaces_map"]
        except KeyError:
            ws = current_app.ws_handler.get(obj.workspace_id)
            workspaces_map = {ws.id: ws.name}
        try:
            workspace_name = workspaces_map[obj.workspace_id]
        except KeyError:
            workspace_name = ""
        return workspace_name


class ProjectVersionSchema(ma.SQLAlchemyAutoSchema):
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.workspace.name)
    name = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.name))
    author = fields.String(attribute="author.username")
    changesets = fields.Method("get_diff_summary")
    files = fields.String()
    created = DateTimeWithZ()
    changes = fields.Method("_changes")

    def get_diff_summary(self, obj):
        return obj.diff_summary()

    def _changes(self, obj):
        changes = {"added": [], "updated": [], "removed": []}
        for file in obj.changes.all():
            if file.change == "create":
                changes["added"].append(FileHistorySchema().dump(file))
            elif file.change in ("update", "update_diff"):
                changes["updated"].append(FileHistorySchema().dump(file))
            elif file.change == "delete":
                changes["removed"].append(FileHistorySchema().dump(file))
        return changes

    class Meta:
        model = ProjectVersion
        exclude = ["id", "ip_address", "ip_geolocation_country", "project", "device_id"]
        load_instance = True


class FullVersionSchema(ma.SQLAlchemyAutoSchema):
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.workspace.name)

    class Meta:
        model = ProjectVersion
        exclude = ["id", "device_id"]
        load_instance = True


class ProjectSchemaForDelete(ma.SQLAlchemyAutoSchema):
    versions = fields.Method("_versions")
    creator_id = fields.Method("_creator_id")

    def _creator_id(self, obj):
        return obj.creator_id

    def _versions(self, obj):
        # this can be a potential issue because we need to create a full dump of project versions
        versions = (
            ProjectVersion.query.filter_by(project_id=obj.id)
            .order_by(ProjectVersion.created.desc())
            .all()
        )
        return FullVersionSchema(many=True).dump(versions)

    class Meta:
        model = Project
        exclude = [
            "uploads",
            "access",
            "creator",
        ]  # these fields will be lost
        load_instance = True


class AdminProjectSchema(ma.SQLAlchemyAutoSchema):
    id = fields.UUID(attribute="Project.id")
    name = fields.Str(attribute="Project.name")
    workspace = fields.Method("_workspace_name")
    workspace_id = fields.Method("_workspace_id")
    version = fields.Function(
        lambda obj: ProjectVersion.to_v_name(obj.Project.latest_version)
    )
    disk_usage = fields.Integer(attribute="Project.disk_usage")
    created = DateTimeWithZ(attribute="Project.created")
    updated = DateTimeWithZ(attribute="Project.updated")
    removed_at = DateTimeWithZ(attribute="Project.removed_at")
    removed_by = fields.Method("_removed_by_user")

    def _removed_by_user(self, obj):
        if not obj.Project.removed_by:
            return
        user = User.query.get(obj.Project.removed_by)
        if user:
            return user.username

    def _workspace_name(self, obj):
        name = getattr(obj, "workspace_name", None)
        if not name:
            name = obj.Project.workspace.name
        return name

    def _workspace_id(self, obj):
        id = getattr(obj, "workspace_id", None)
        if not id:
            id = obj.Project.workspace.id
        return id


class UserWorkspaceSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    storage = fields.Integer()
    disk_usage = fields.Function(lambda obj: obj.disk_usage())
    project_count = fields.Function(lambda obj: obj.project_count())
    role = fields.Method("_user_role")

    def _user_role(self, obj):
        if not self.context.get("user"):
            return
        return obj.get_user_role(self.context.get("user"))


class ProjectInvitationAccessSchema(Schema):
    expires_at = fields.String()


class StrOrInt(fields.Field):
    """Custom field type for validating both str or int datatype"""

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str) or isinstance(value, int):
            return value
        else:
            raise ValidationError("Field should be str or int")


class ProjectAccessDetailSchema(Schema):
    id = StrOrInt()
    email = fields.String()
    role = fields.String()
    username = fields.String()
    name = fields.String()
    project_permission = fields.String()
    type = fields.String()
    invitation = fields.Nested(ProjectInvitationAccessSchema())


class ProjectVersionListSchema(ma.SQLAlchemyAutoSchema):
    project_name = fields.Function(lambda obj: obj.project.name)
    namespace = fields.Function(lambda obj: obj.project.workspace.name)
    name = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.name))
    author = fields.String(attribute="author.username")
    created = DateTimeWithZ()
    changes = fields.Method("_changes")
    project_size = fields.Integer()

    def _changes(self, obj):
        result = obj.changes_count()
        data = {
            "added": result.get(PushChangeType.CREATE.value, 0),
            "updated": result.get(PushChangeType.UPDATE.value, 0),
            "updated_diff": result.get(PushChangeType.UPDATE_DIFF.value, 0),
            "removed": result.get(PushChangeType.DELETE.value, 0),
        }
        return data

    class Meta:
        model = ProjectVersion
        exclude = [
            "id",
            "ip_address",
            "ip_geolocation_country",
            "project",
            "device_id",
            "user_agent",
        ]
        load_instance = True
