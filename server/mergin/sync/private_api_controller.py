# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from blinker import signal
from connexion import NoContent
from flask import render_template, request, current_app, jsonify, abort
from flask_login import current_user
from sqlalchemy.orm import defer
from sqlalchemy import text, and_, desc, asc

from ..app import db
from ..auth import auth_required
from ..auth.models import User, UserProfile
from .forms import AccessPermissionForm
from .models import Project, AccessRequest, ProjectRole, RequestStatus, ProjectVersion
from .schemas import (
    ProjectListSchema,
    ProjectAccessRequestSchema,
    AdminProjectSchema,
    ProjectAccessSchema,
    ProjectAccessDetailSchema,
    ProjectVersionListSchema,
)
from .permissions import (
    require_project_by_uuid,
    ProjectPermissions,
    check_workspace_permissions,
)
from ..utils import parse_order_params, split_order_param, get_order_param

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

    access_request = (
        AccessRequest.query.filter_by(
            project_id=project.id, requested_by=current_user.id
        )
        .filter(AccessRequest.resolved_at.is_(None))
        .first()
    )
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
                link=f"{request.url_root.rstrip('/')}/projects/{namespace}/{project.name}/collaborators",
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
def decline_project_access_request(request_id):  # noqa: E501
    access_request = (
        AccessRequest.query.join(AccessRequest.project)
        .filter(
            AccessRequest.id == request_id,
            AccessRequest.resolved_at.is_(None),
            Project.removed_at.is_(None),
        )
        .first_or_404()
    )
    project = access_request.project
    project_role = ProjectPermissions.get_user_project_role(project, current_user)
    if (
        project_role == ProjectRole.OWNER
        or current_user.id == access_request.requested_by
    ):
        access_request.resolve(RequestStatus.DECLINED, current_user.id)
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
        .filter(
            AccessRequest.id == request_id,
            AccessRequest.resolved_at.is_(None),
            Project.removed_at.is_(None),
        )
        .first_or_404()
    )
    project = access_request.project
    project_role = ProjectPermissions.get_user_project_role(project, current_user)
    if project_role == ProjectRole.OWNER:
        project_access_granted.send(
            access_request.project, user_id=access_request.requested_by
        )
        access_request.accept(permission)
        return "", 200
    abort(403, "You don't have permissions to accept project access request")


@auth_required
def get_project_access_requests(page, per_page, order_params=None, project_name=None):
    """Paginated list of active project access requests initiated by current user in session"""
    requests_query = current_app.ws_handler.access_requests_query()
    access_requests = requests_query.filter(
        AccessRequest.requested_by == current_user.id,
        AccessRequest.resolved_at.is_(None),
        Project.removed_at.is_(None),
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
    """Paginated list of active incoming project access requests to workspace"""
    if not check_workspace_permissions(namespace, current_user, "admin"):
        abort(403, "You don't have permissions to list project access requests")
    ws = current_app.ws_handler.get_by_name(namespace)
    access_requests = AccessRequest.query.join(AccessRequest.project).filter(
        Project.workspace_id == ws.id,
        AccessRequest.resolved_at.is_(None),
        Project.removed_at.is_(None),
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
def list_projects(page, per_page, order_params=None, like=None):  # noqa: E501
    projects = current_app.ws_handler.projects_query(like)
    # do not fetch from db what is not needed
    projects = projects.options(
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
                order_by_params.append(
                    text(f"workspace_name {order_param.direction.value}")
                )
            else:
                order_by_params.append(get_order_param(Project, order_param))
        projects = projects.order_by(*order_by_params)

    result = projects.paginate(page, per_page).items
    total = projects.paginate(page, per_page).total
    data = AdminProjectSchema(many=True).dump(result)
    data = {"items": data, "count": total}
    return data, 200


@auth_required(permissions=["admin"])
def restore_project(id):  # noqa: E501
    """Restore project marked for removal"""
    project = (
        Project.query.filter_by(id=id)
        .filter(Project.storage_params.isnot(None))
        .first_or_404()
    )
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
    project = (
        Project.query.filter_by(id=id)
        .filter(Project.storage_params.isnot(None))
        .first_or_404()
    )
    if not project.removed_at:
        abort(400, "Failed to remove: Project is still active")
    project.delete()
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
    return NoContent, 200


@auth_required
def update_project_access(id: str):
    """Modify shared project access

    :param id: Project uuid
    """
    project = require_project_by_uuid(id, ProjectPermissions.Update)

    if "public" in request.json:
        project.access.public = request.json["public"]

    if "user_id" in request.json and "role" in request.json:
        user = User.query.filter_by(
            id=request.json["user_id"], active=True
        ).first_or_404("User does not exist")

        if request.json["role"] == "none":
            project.access.unset_role(user.id)
        else:
            project.access.set_role(user.id, ProjectRole(request.json["role"]))
            project_access_granted.send(project, user_id=user.id)
    db.session.commit()
    return ProjectAccessSchema().dump(project.access), 200


@auth_required
def get_project_access(id: str):
    """Get list of users with access to project"""
    project = require_project_by_uuid(id, ProjectPermissions.Read)
    result = current_app.ws_handler.project_access(project)
    data = ProjectAccessDetailSchema(many=True).dump(result)
    return data, 200
