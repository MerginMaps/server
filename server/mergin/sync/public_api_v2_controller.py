# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime
from connexion import NoContent, request
from flask import abort, jsonify
from flask_login import current_user

from mergin.sync.forms import project_name_validation

from .schemas import ProjectMemberSchema
from .workspace import WorkspaceRole
from ..app import db
from ..auth import auth_required
from ..auth.models import User
from .models import Project, ProjectRole, ProjectMember
from .permissions import ProjectPermissions, require_project_by_uuid
from .private_api_controller import project_access_granted


@auth_required
def schedule_delete_project(id):
    """Schedule deletion of the project.
    Celery job `mergin.sync.tasks.remove_projects_backups` does the
    rest.
    """
    project = require_project_by_uuid(id, ProjectPermissions.Delete)
    project.removed_at = datetime.utcnow()
    project.removed_by = current_user.id
    db.session.commit()

    return NoContent, 204


@auth_required
def delete_project_now(id):
    """Delete the project immediately"""
    project = require_project_by_uuid(id, ProjectPermissions.Delete, scheduled=True)
    project.delete()

    return NoContent, 204


@auth_required
def update_project(id):
    """Rename project"""
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    new_name = request.json["name"].strip()

    if not new_name:
        abort(400, "Project name cannot be empty")
    validation = project_name_validation(new_name)
    if validation:
        return (
            jsonify(code="InvalidProjectName", detail=validation),
            400,
        )
    new_name_exists = Project.query.filter_by(
        workspace_id=project.workspace_id, name=new_name
    ).first()
    if new_name_exists:
        abort(409, "Name already exist within workspace")

    project.name = new_name.strip()
    db.session.commit()

    return NoContent, 204


@auth_required
def get_project_collaborators(id):
    """Get project collaborators, with both direct role and inherited role from workspace"""
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    project_members = []
    for user, workspace_role in project.workspace.members():
        project_role = project.get_role(user.id)
        if workspace_role != WorkspaceRole.GUEST or project_role is not None:
            project_members.append(
                ProjectMember(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    project_role=project_role,
                    workspace_role=workspace_role,
                    role=ProjectPermissions.get_user_project_role(project, user),
                )
            )

    data = ProjectMemberSchema(many=True).dump(project_members)
    return data, 200


@auth_required
def add_project_collaborator(id):
    """Add project collaborator"""
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    user = User.get_by_login(request.json["user"])
    if not user:
        abort(404)

    if project.get_role(user.id):
        abort(409, "User is already a project member")

    project.set_role(user.id, ProjectRole(request.json["role"]))
    db.session.commit()
    project_access_granted.send(project, user_id=user.id)
    data = ProjectMemberSchema().dump(project.get_member(user.id))
    return data, 201


@auth_required
def update_project_collaborator(id, user_id):
    """Update project collaborator"""
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    user = User.query.filter_by(id=user_id, active=True).first_or_404()
    if not project.get_role(user_id):
        abort(404)

    project.set_role(user.id, ProjectRole(request.json["role"]))
    db.session.commit()
    data = ProjectMemberSchema().dump(project.get_member(user.id))
    return data, 200


@auth_required
def remove_project_collaborator(id, user_id):
    """Remove project collaborator"""
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    if not project.get_role(user_id):
        abort(404)

    project.unset_role(user_id)
    db.session.commit()
    return NoContent, 204
