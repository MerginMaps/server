# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from marshmallow import fields

from .. import ma
from .models import User, UserProfile


class UserProfileSchema(ma.ModelSchema):
    name = ma.Function(
        lambda obj:
        f'{obj.first_name if obj.first_name else ""} {obj.last_name if obj.last_name else ""}'.strip(), dump_only=True)
    storage = fields.Method("get_storage", dump_only=True)
    disk_usage = fields.Method("get_disk_usage", dump_only=True)
    organisations = fields.Method("get_user_organisations", dump_only=True)
    has_project = fields.Method("_has_project", dump_only=True)

    def get_storage(self, obj):
        from ..models.db_models import Namespace

        ns = Namespace.query.filter_by(name=obj.user.username).first()
        return ns.storage

    def get_disk_usage(self, obj):
        from ..models.db_models import Namespace

        ns = Namespace.query.filter_by(name=obj.user.username).first()
        return ns.disk_usage()

    def get_user_organisations(self, obj):
        """ Return dictionary of organisation name: role for organisations user is member of """
        from ..organisation.models import Organisation
        org_map = {}
        organisations = Organisation.find_by_member_id(obj.user_id)
        for org in organisations:
            org_map[org.name] = org.get_member_role(obj.user_id)
        return org_map

    def _has_project(self, obj):
        from ..models.db_models import Project

        projects_count = Project.query.filter(Project.creator_id == obj.user.id).filter_by(
            namespace=obj.user.username).count()
        return projects_count > 0

    class Meta:
        model = UserProfile


class UserSchema(ma.ModelSchema):
    profile = fields.Nested(UserProfileSchema, exclude=("user", ))
    account = fields.Method("get_account", dump_only=True)

    def get_account(self, obj):
        from ..models.schemas import AccountSchema
        from ..models.db_models import Namespace, Account, Project

        account = Account.query.filter_by(type='user', owner_id=obj.id).first()
        return AccountSchema().dump(account)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'active', 'is_admin', 'profile', 'account', 'verified_email')


class UserSearchSchema(ma.ModelSchema):
    profile = fields.Nested(UserProfileSchema, only=(
        'first_name', 'last_name'))

    class Meta:
        model = User
        fields = ('id', 'username', 'profile')


class AccountSearchSchema(ma.ModelSchema):
    id = fields.Integer()
    type = fields.String()
    name = fields.Method("get_name")

    def get_name(self, obj):
        if obj.type == "user":
            return obj.username
        else:
            return obj.name

