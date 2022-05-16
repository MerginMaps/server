# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from marshmallow import fields
from .. import ma
from ..models.db_models import Project, Namespace
from ..auth.models import User
from .models import Organisation, OrganisationInvitation


class OrganisationSchema(ma.ModelSchema):
    name = fields.Str()
    disk_usage = fields.Method("get_disk_usage")
    project_count = fields.Method("get_project_count")
    owners = fields.Method("get_owners")
    admins = fields.Method("get_admins")
    writers = fields.Method("get_writers")
    readers = fields.Method("get_readers")
    storage = fields.Method("get_storage")
    role = fields.Method("get_role", dump_only=True)
    account = fields.Method("get_account", dump_only=True)

    def get_owners(self, obj):
        return self.get_access_usernames(obj, 'owners')

    def get_admins(self, obj):
        return self.get_access_usernames(obj, 'admins')

    def get_writers(self, obj):
        return self.get_access_usernames(obj, 'writers')

    def get_readers(self, obj):
        return self.get_access_usernames(obj, 'readers')

    def get_access_usernames(self, obj, role):
        users = User.query.filter(User.id.in_(getattr(obj, role))).all()
        return [u.username for u in users]

    def get_disk_usage(self, obj):
        return sum([p.disk_usage for p in Project.query.filter_by(namespace=obj.name)])

    def get_project_count(self, obj):
        return Project.query.filter_by(namespace=obj.name).count()

    def get_storage(self, obj):
        ns = Namespace.query.filter_by(name=obj.name).first()
        return ns.storage

    def get_role(self, obj):
        if self.context and 'user' in self.context:
            return obj.get_member_role(self.context['user'].id)
        else:
            return "unknown"

    def _is_owner(self, obj):
        return self.context and 'user' in self.context and obj.get_member_role(self.context['user'].id) == "owner"

    def _is_mergin_admin(self, obj):
        return self.context and 'user' in self.context and self.context['user'].is_admin

    def get_account(self, obj):
        from ..models.db_models import Account
        from ..models.schemas import AccountSchema
        account = Account.query.filter_by(type='organisation', owner_id=obj.id).first()
        if self._is_owner(obj) or self._is_mergin_admin(obj):
            return AccountSchema().dump(account)
        else:
            return AccountSchema(only=('email',)).dump(account)  # do not send private information

    class Meta:
        model = Organisation
        exclude = ('invitations', )


class OrganisationInvitationSchema(ma.ModelSchema):
    org_name = fields.Str()
    username = fields.Str()

    class Meta:
        model = OrganisationInvitation
