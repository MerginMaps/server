# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from blinker import signal
from connexion import NoContent
from flask import render_template, request, current_app, jsonify, abort
from flask_login import current_user
from sqlalchemy.orm import defer
from sqlalchemy.sql import literal, select, label
from sqlalchemy import text

from .. import db
from ..auth import auth_required
from ..auth.models import User, UserProfile
from .forms import AccessPermissionForm
from .models import Project, AccessRequest, ProjectRole
from .schemas import ProjectListSchema, ProjectAccessRequestSchema, AdminProjectSchema
from .permissions import (
    require_project_by_uuid,
    ProjectPermissions,
    check_workspace_permissions,
)
from .utils import get_project_path, split_order_param, get_order_param

from ..utils import parse_order_params

project_access_granted = signal("project_access_granted")


@auth_required
def create_project_access_request(namespace, project_name):  # noqa: E501
    from ..celery import send_email_async

    workspace = current_app.ws_handler.get_by_name(namespace)
    project = Project.query.filter(
        Project.name == project_name,
        Project.workspace_id == workspace.id,
        Project.removed_at.is_(None),
    ).first_or_404()
    if current_user.id in project.access.readers:
        abort(409, "You already have access to project")

    access_request = AccessRequest.query.filter_by(
        project_id=project.id, user_id=current_user.id
    ).first()
    if access_request:
        abort(409, "Project access request already exists")

    access_request = AccessRequest(project, current_user.id)
    db.session.add(access_request)
    db.session.commit()
    # notify project owners
    owners = (
        User.query.join(UserProfile)
        .filter(User.verified_email, User.id.in_(project.access.owners))
        .filter(UserProfile.receive_notifications)
        .all()
    )
    for owner in owners:
        email_data = {
            "subject": "Project access requested",
            "html": render_template(
                "email/project_access_request.html",
                expire=access_request.expire,
                link=f"{request.url_root.rstrip('/')}/projects/{namespace}/{project.name}/settings",
                user=current_user.username,
                username=owner.username,
                project_name=f"{namespace}/{project.name}",
            ),
            "recipients": [owner.email],
            "sender": current_app.config["MAIL_DEFAULT_SENDER"],
        }
        send_email_async.delay(**email_data)
    return "", 200


@auth_required
def delete_project_access_request(request_id):  # noqa: E501
    access_request = (
        AccessRequest.query.join(AccessRequest.project)
        .filter(AccessRequest.id == request_id, Project.removed_at.is_(None))
        .first_or_404()
    )

    if (
        current_user.id in access_request.project.access.owners
        or current_user.id == access_request.project.creator
        or current_user.id == access_request.user_id
    ):
        AccessRequest.query.filter(AccessRequest.id == request_id).delete()
        db.session.commit()
        return "", 200
    abort(403, "You don't have permissions to remove project access request")


@auth_required
def accept_project_access_request(request_id):
    form = AccessPermissionForm()
    if not form.validate():
        return jsonify(form.errors), 400

    permission = form.permissions.data
    access_request = (
        AccessRequest.query.join(AccessRequest.project)
        .filter(AccessRequest.id == request_id, Project.removed_at.is_(None))
        .first_or_404()
    )
    if (
        current_user.id in access_request.project.access.owners
        or current_user.id == access_request.project.creator
    ):
        project_access_granted.send(
            access_request.project, user_id=access_request.user_id
        )
        access_request.accept(permission)
        return "", 200
    abort(403, "You don't have permissions to accept project access request")


@auth_required
def get_project_access_requests(page, per_page, order_params=None, project_name=None):
    """Paginated list of project access requests initiated by current user in session"""
    access_requests = AccessRequest.query.join(AccessRequest.project).filter(
        AccessRequest.user_id == current_user.id, Project.removed_at.is_(None)
    )

    if project_name:
        access_requests = access_requests.filter(Project.name == project_name)

    if order_params:
        order_by_params = parse_order_params(AccessRequest, order_params)
        access_requests = access_requests.order_by(*order_by_params)

    result = access_requests.paginate(page, per_page).items
    total = access_requests.paginate(page, per_page).total
    data = ProjectAccessRequestSchema(many=True).dump(result)
    data = {"items": data, "count": total}
    return data, 200


@auth_required
def list_namespace_project_access_requests(
    namespace, page, per_page, order_params=None, project_name=None
):
    """Paginated list of incoming project access requests to workspace"""
    if not check_workspace_permissions(namespace, current_user, "admin"):
        abort(403, "You don't have permissions to list project access requests")
    ws = current_app.ws_handler.get_by_name(namespace)
    access_requests = AccessRequest.query.join(AccessRequest.project).filter(
        Project.workspace_id == ws.id, Project.removed_at.is_(None)
    )

    if project_name:
        access_requests = access_requests.filter(Project.name == project_name)

    if order_params:
        order_by_params = parse_order_params(AccessRequest, order_params)
        access_requests = access_requests.order_by(*order_by_params)

    result = access_requests.paginate(page, per_page).items
    total = access_requests.paginate(page, per_page).total
    data = ProjectAccessRequestSchema(many=True).dump(result)
    data = {"items": data, "count": total}
    return data, 200


@auth_required(permissions=["admin"])
def list_projects(
    page, per_page, order_params=None, name=None, workspace=None
):  # noqa: E501
    projects = current_app.ws_handler.projects_query(name, workspace)
    # do not fetch from db what is not needed
    projects = projects.options(
        defer(Project.files),
        defer(Project.storage_params),
        defer(Project.tags),
    )
    if order_params:
        order_by_params = []
        for param in order_params.split(","):
            order_param = split_order_param(param)
            if not order_param:
                continue
            if order_param.name == "workspace":
                order_by_params.append(text(f"workspace_name {order_param.direction}"))
            else:
                order_by_params.append(get_order_param(Project, order_param))
        projects = projects.order_by(*order_by_params)

    result = projects.paginate(page, per_page).items
    total = projects.paginate(page, per_page).total
    data = AdminProjectSchema(many=True).dump(result)
    data = {"projects": data, "count": total}
    return data, 200


@auth_required(permissions=["admin"])
def restore_project(id):  # noqa: E501
    """Restore project marked for removal"""
    project = Project.query.get_or_404(id)
    if not project.removed_at:
        return "", 201
    if not project.workspace.is_active:
        abort(400, "Failed to restore: Project workspace is not active")
    project.removed_at = None
    project.removed_by = None
    db.session.commit()
    return "", 201


@auth_required(permissions=["admin"])
def force_project_delete(id):  # noqa: E501
    project = Project.query.get_or_404(id)
    if not project.removed_at:
        abort(400, "Failed to remove: Project is still active")
    project.storage.delete()
    db.session.delete(project)
    db.session.commit()
    return "", 204


@auth_required
def template_projects():  # pylint: disable=W0612
    projects = Project.query.filter(
        Project.creator.has(username="TEMPLATES"), Project.removed_at.is_(None)
    ).all()
    ws_ids = [p.workspace_id for p in projects]
    workspaces_map = {w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)}
    ctx = {"workspaces_map": workspaces_map}
    project_schema = ProjectListSchema(
        many=True,
        only=(
            "id",
            "name",
            "namespace",
            "version",
        ),
        context=ctx,
    )
    return jsonify(project_schema.dump(projects)), 200


@auth_required
def unsubscribe_project(id):  # pylint: disable=W0612
    """Unsubscribe user from shared project

    Unsubscribe from the shared project if user is reader/writer, access to project is removed

    :param id: Project uuid
    :type id: str
    :rtype: None
    """
    from ..celery import send_email_async

    project = require_project_by_uuid(id, ProjectPermissions.Read)
    current_role = project.access.get_role(current_user.id)
    if not current_role:
        return NoContent, 200  # nothing to do so request is idempotent

    # prevent project owner to self-remove
    if current_role == ProjectRole.OWNER:
        abort(400, "Owner cannot leave a project")

    project.access.unset_role(current_user.id)
    db.session.add(project)
    db.session.commit()
    # notify owners and the user who unsubscribed
    project_path = get_project_path(project)
    recipients = (
        UserProfile.query.filter(
            UserProfile.user_id.in_(project.access.owners + [current_user.id])
        )
        .filter(UserProfile.receive_notifications)
        .all()
    )
    for profile in recipients:
        if not profile.user.verified_email:
            continue
        html = render_template(
            "email/project_unsubscribe.html",
            project_path=project_path,
            recipient=profile.user.username,
            username=current_user.username,
        )
        email_data = {
            "subject": f"Access to mergin project {project_path} has been modified",
            "html": html,
            "recipients": [profile.user.email],
            "sender": current_app.config["MAIL_DEFAULT_SENDER"],
        }
        send_email_async.delay(**email_data)
    return NoContent, 200


@auth_required
def update_project_access(id: str):
    """Modify shared project access

    :param id: Project uuid
    :rtype: None
    """
    project = require_project_by_uuid(id, ProjectPermissions.Update)
    user = User.query.filter_by(id=request.json["user_id"], active=True).first_or_404(
        "User does not exist"
    )
    # prevent to remove ownership of project creator
    if user.id == project.creator_id:
        abort(400, "Ownership of project creator cannot be removed")

    if request.json["role"] == "none":
        project.access.unset_role(user.id)
    else:
        project.access.set_role(user.id, ProjectRole(request.json["role"]))
        project_access_granted.send(project, user_id=user.id)
    db.session.commit()
    return NoContent, 200
