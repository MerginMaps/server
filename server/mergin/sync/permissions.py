# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from functools import wraps
from typing import Optional
from flask import abort, current_app
from flask_login import current_user

from .utils import is_valid_uuid
from ..auth.models import User
from .models import ProjectAccess, Project, Upload


def _is_superuser(f):
    """Decorator to bypass project permissions checks if passed user is a superuser"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, User) and arg.is_authenticated and arg.is_admin:
                return True
        return f(*args, **kwargs)

    return wrapper


class ProjectPermissions:
    class Base:
        @classmethod
        def check(cls, project: Project, user: User) -> bool:
            """Basic check for any permission"""
            # this means project was permanently 'removed'
            if project.storage_params is None:
                return False

            if not user.is_authenticated:
                return False

            if project.removed_at:
                return False
            return True

    class Read(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            # public active projects can be access by anyone
            if project.access.public and not project.removed_at:
                return True

            return super().check(project, user) and (
                (user.id in project.access.readers)
                or (check_project_workspace_permissions(project, user, "read"))
            )

        @classmethod
        def query(cls, user, as_admin=True, public=True):
            if user.is_authenticated and user.is_admin and as_admin:
                return Project.query
            query = Project.access.has(public=public)
            if user.is_authenticated and user.active:
                all_workspaces = current_app.ws_handler.list_user_workspaces(
                    user.username, active=True
                )
                user_workspace_ids = [
                    ws.id
                    for ws in all_workspaces
                    if ws.user_has_permissions(user, "read")
                ]
                if public:
                    query = query | Project.access.has(
                        ProjectAccess.readers.contains([user.id])
                        | Project.workspace_id.in_(user_workspace_ids)
                    )
                else:
                    query = Project.access.has(
                        ProjectAccess.readers.contains([user.id])
                        | Project.workspace_id.in_(user_workspace_ids)
                    )
            return (
                Project.query.filter(query)
                .filter(Project.storage_params.isnot(None))
                .filter(Project.removed_at.is_(None))
            )

    class Edit(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            return super().check(project, user) and (
                (
                    user.id
                    in project.access.writers  # EDITOR version 1: user.id in project.access.editors
                    or check_project_workspace_permissions(project, user, "edit")
                )
            )

    class Upload(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            return super().check(project, user) and (
                (
                    user.id in project.access.writers
                    or check_project_workspace_permissions(project, user, "write")
                )
            )

    class Update(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            return super().check(project, user) and (
                (
                    user.id in project.access.owners
                    or check_project_workspace_permissions(project, user, "admin")
                )
            )

    class Delete(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            return super().check(project, user) and (
                (
                    user.id in project.access.owners
                    or check_project_workspace_permissions(project, user, "admin")
                )
            )

    class All(Base):
        @classmethod
        @_is_superuser
        def check(cls, project, user):
            return super().check(project, user) and (
                (
                    user.id in project.access.owners
                    or check_project_workspace_permissions(project, user, "admin")
                )
            )


def require_project(ws, project_name, permission):
    workspace = current_app.ws_handler.get_by_name(ws)
    if not workspace:
        abort(404)
    if not workspace.is_active and not current_user.is_admin:
        abort(404, "Workspace doesn't exist")
    project = (
        Project.query.filter_by(name=project_name, workspace_id=workspace.id)
        .filter(Project.storage_params.isnot(None))
        .filter(Project.removed_at.is_(None))
        .first_or_404()
    )
    if not permission.check(project, current_user):
        abort(403, "You do not have permissions for this project")
    return project


def require_project_by_uuid(uuid, permission, scheduled=False):
    if not is_valid_uuid(uuid):
        abort(404)

    project = Project.query.filter_by(id=uuid).filter(
        Project.storage_params.isnot(None)
    )
    if not scheduled:
        project = project.filter(Project.removed_at.is_(None))
    project = project.first_or_404()
    workspace = project.workspace
    if not workspace:
        abort(404)
    if not workspace.is_active and not current_user.is_admin:
        abort(404, "Workspace doesn't exist")
    if not permission.check(project, current_user):
        abort(403, "You do not have permissions for this project")
    return project


def get_upload(transaction_id):
    upload = Upload.query.get_or_404(transaction_id)
    # upload to 'removed' projects is forbidden
    if upload.project.removed_at:
        abort(404)

    if upload.user_id != current_user.id:
        abort(403, "You do not have permissions for ongoing upload")

    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", transaction_id)
    return upload, upload_dir


def projects_query(permission, as_admin=True, public=True):
    return permission.query(current_user, as_admin, public)


def check_project_workspace_permissions(project, user, permissions):
    """check if user has permission to workspace
    :param project: project
    :type project: project

    :param user: user
    :type user: User

    :param permissions: permissions to access to workspace
    :type permissions: str

    :return: whether user has desired permissions in workspace
    :rtype: bool
    """
    if user.is_anonymous or not user.active:
        return False
    workspace = project.workspace
    if not workspace:
        return False
    return workspace.user_has_permissions(user, permissions, project)


def check_workspace_permissions(ws, user, permissions):
    """check if user has permission to namespace

    :param ws: namespace
    :type ws: str

    :param user: user
    :type user: User

    :param permissions: permissions to access to namespace
    :type permissions: str

    :return: whether user has desired permissions in namespace
    :rtype: bool
    """
    if user.is_anonymous or not user.active:
        return False
    workspace = current_app.ws_handler.get_by_name(ws)
    if not workspace:
        return False
    return workspace.user_has_permissions(user, permissions)


def get_user_project_role(project: Project, user: User) -> Optional[str]:
    """Get the highest role of user for given project.
    It can be based on local project settings or some global workspace settings.
    """
    if ProjectPermissions.All.check(project, user):
        return "owner"
    if ProjectPermissions.Upload.check(project, user):
        return "writer"
    if ProjectPermissions.Edit.check(project, user):
        return "editor"
    if ProjectPermissions.Read.check(project, user):
        return "reader"
