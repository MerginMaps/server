# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from marshmallow import fields
from flask_login import current_user

from ..app import DateTimeWithZ, ma
from .permissions import ProjectPermissions
from .models import (
    Project,
    ProjectVersion,
)
from ..utils import get_schema_fields_map


class ProjectSchema(ma.SQLAlchemyAutoSchema):
    id = fields.UUID()
    name = fields.String()
    version = fields.Function(lambda obj: ProjectVersion.to_v_name(obj.latest_version))
    public = fields.Boolean()
    size = fields.Integer(attribute="disk_usage")

    created_at = DateTimeWithZ(attribute="created")
    updated_at = DateTimeWithZ(attribute="updated")

    workspace = fields.Function(
        lambda obj: {"id": obj.workspace.id, "name": obj.workspace.name}
    )
    role = fields.Method("_role")

    def _role(self, obj):
        role = ProjectPermissions.get_user_project_role(obj, current_user)
        return role.value if role else None

    class Meta:
        model = Project
        load_instance = True
        fields = (
            "id",
            "name",
            "version",
            "public",
            "size",
            "created_at",
            "updated_at",
            "workspace",
            "role",
        )


ProjectSchema.field_map = get_schema_fields_map(ProjectSchema)
