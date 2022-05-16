# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from flask_login import current_user
from ..organisation import Organisation


class OrganisationPermissions:
    """ Get or check organisation by permission """

    @staticmethod
    def _query(user, field):
        """ return query of organisation """
        if user.is_authenticated and user.is_admin:
            return Organisation.query
        if not user.is_authenticated:
            return Organisation.query.filter(False)
        return Organisation.query.filter(field.any(user.id))

    class Owner:
        @staticmethod
        def query(user):
            return OrganisationPermissions._query(user, Organisation.owners)

    class Admin:
        @staticmethod
        def query(user):
            return OrganisationPermissions._query(user, Organisation.admins)

    class Writer:
        @staticmethod
        def query(user):
            return OrganisationPermissions._query(user, Organisation.writers)

    class Reader:
        @staticmethod
        def query(user):
            return OrganisationPermissions._query(user, Organisation.readers)


def organisations_query(permission):
    return permission.query(current_user)
