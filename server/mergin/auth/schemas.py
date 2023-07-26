# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from datetime import timedelta

from flask import current_app
from marshmallow import fields

from .. import ma
from .models import User, UserProfile
from ..app import DateTimeWithZ


class UserProfileSchema(ma.SQLAlchemyAutoSchema):
    name = ma.Function(
        lambda obj: f'{obj.first_name if obj.first_name else ""} {obj.last_name if obj.last_name else ""}'.strip(),
        dump_only=True,
    )
    storage = fields.Method("get_storage", dump_only=True)
    disk_usage = fields.Method("get_disk_usage", dump_only=True)
    has_project = fields.Method("_has_project", dump_only=True)

    def get_storage(self, obj):
        # DEPRECATED functionality - kept for the backward-compatibility
        ws = current_app.ws_handler.get_by_name(obj.user.username)
        if ws:
            return ws.storage

    def get_disk_usage(self, obj):
        # DEPRECATED functionality - kept for the backward-compatibility
        ws = current_app.ws_handler.get_by_name(obj.user.username)
        if ws:
            return ws.disk_usage()

    def _has_project(self, obj):
        # DEPRECATED functionality - kept for the backward-compatibility
        from ..sync.models import Project

        ws = current_app.ws_handler.get_by_name(obj.user.username)
        if ws:
            projects_count = (
                Project.query.filter(Project.creator_id == obj.user.id)
                .filter_by(workspace_id=ws.id)
                .count()
            )
            return projects_count > 0
        return False

    class Meta:
        model = UserProfile
        load_instance = True


class UserSchema(ma.SQLAlchemyAutoSchema):
    """User schema with full information"""

    profile = fields.Nested(UserProfileSchema())
    scheduled_removal = DateTimeWithZ(attribute="removal_at", dump_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "active",
            "is_admin",
            "verified_email",
            "profile",
            "scheduled_removal",
        )
        load_instance = True


class UserSearchSchema(ma.SQLAlchemyAutoSchema):
    """User schema for public search queries"""

    profile = fields.Nested(UserProfileSchema(), only=("first_name", "last_name"))

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "profile",
        )
        load_instance = True


class UserInfoSchema(ma.SQLAlchemyAutoSchema):
    """User schema with full information"""

    first_name = fields.String(attribute="profile.first_name")
    last_name = fields.String(attribute="profile.last_name")
    receive_notifications = fields.Boolean(attribute="profile.receive_notifications")
    registration_date = DateTimeWithZ(attribute="profile.registration_date")
    name = fields.Function(lambda obj: obj.profile.name())

    class Meta:
        model = User
        exclude = (
            "active",
            "inactive_since",
            "is_admin",
            "passwd",
        )
        load_instance = True
