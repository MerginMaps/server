# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import os
from flask import abort
from flask_login import current_user
from sqlalchemy import or_

from .auth.models import User
from .organisation import Organisation
from .organisation.permission import organisations_query, OrganisationPermissions
from .models.db_models import ProjectAccess, Project, Upload, Namespace


class ProjectPermissions:
    class Read:
        @staticmethod
        def check(project, user):
            pa = project.access
            return pa.public or (user.is_authenticated and (user.is_admin or user.id in pa.readers)) or (check_namespace_permissions(project.namespace, user, "read"))

        @staticmethod
        def query(user, as_admin=True, public=True):
            if user.is_authenticated and user.is_admin and as_admin:
                return Project.query
            query = Project.access.has(public=public)
            if user.is_authenticated:
                orgs = Organisation.query.with_entities(Organisation.name).filter(
                    or_(Organisation.admins.contains([user.id]), Organisation.readers.contains([user.id]),
                        Organisation.writers.contains([user.id]), Organisation.owners.contains([user.id])))
                if public:
                    query = query | Project.access.has(ProjectAccess.readers.contains([user.id]) | Project.namespace.in_(orgs))
                else:
                    query = Project.access.has(ProjectAccess.readers.contains([user.id]) | Project.namespace.in_(orgs))
            return Project.query.filter(query)

    class Upload:
        @staticmethod
        def check(project, user):
            return user.is_authenticated and (user.id in project.access.writers or check_namespace_permissions(project.namespace, user, "write"))

    class Update:
        @staticmethod
        def check(project, user):
            return user.is_authenticated and (user.is_admin or user.id in project.access.owners or user.username in project.access.owners or check_namespace_permissions(project.namespace, user, "write"))

    class Delete:
        @staticmethod
        def check(project, user):
            return user.is_authenticated and (user.is_admin or user.id in project.access.owners or check_namespace_permissions(project.namespace, user, "write"))

    class All:
        @staticmethod
        def check(project, user):
            return user.is_authenticated and (user.is_admin or user.id in project.access.owners or check_namespace_permissions(project.namespace, user, "admin"))


def require_project(ns, project_name, permission):
    project = Project.query.filter_by(name=project_name, namespace=ns).first_or_404()
    if not permission.check(project, current_user):
        abort(403, "You do not have permissions for this project")
    return project


def get_upload(transaction_id):
    upload = Upload.query.get_or_404(transaction_id)
    if upload.user_id != current_user.id:
        abort(403, "You do not have permissions for ongoing upload")

    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", transaction_id)
    return upload, upload_dir


def projects_query(permission, as_admin=True, public=True):
    return permission.query(current_user, as_admin, public)


def check_namespace_permissions(ns, user, permissions):
    """ check if user has permission to namespace granted from organisation or by itself

    :param ns: namespace
    :type ns: str

    :param user: user
    :type user: User

    :param permissions: permissions to access to namespace
    :type permissions: str

    :return: true if user has same username with namespace, otherwise check for organisation
    :rtype: bool
    """
    if user.is_anonymous:
        return False
    if user.username == ns:
        return True
    organisation = Organisation.query.filter_by(name=ns).first()
    if not organisation:
        return False
    if permissions == "read":
        return user.id in organisation.readers
    elif permissions == "write":
        return user.id in organisation.writers
    elif permissions == "admin":
        return user.id in organisation.admins
    else:
        return False


def namespaces_query(permission):
    return permission.query(current_user)


class NamespacePermissions:
    """ Get or check namespace by permission """

    @staticmethod
    def _query(user, permission):
        """ return query of organisation """
        if current_user.is_authenticated and current_user.is_admin:
            return Namespace.query
        if not current_user.is_authenticated:
            return Namespace.query.filter(False)
        namespaces = [org.name for org in organisations_query(permission)]
        namespaces.append(user.username)
        return Namespace.query.filter(Namespace.name.in_(namespaces)).all()

    class Owner:
        @staticmethod
        def query(user):
            return NamespacePermissions._query(user, OrganisationPermissions.Owner)

    class Admin:
        @staticmethod
        def query(user):
            return NamespacePermissions._query(user, OrganisationPermissions.Admin)

    class Writer:
        @staticmethod
        def query(user):
            return NamespacePermissions._query(user, OrganisationPermissions.Writer)

    class Reader:
        @staticmethod
        def query(user):
            return NamespacePermissions._query(user, OrganisationPermissions.Reader)