# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import uuid
import gevent
import logging
import os
import psycopg2
from connexion import NoContent, request
from datetime import datetime, timedelta, timezone
from flask import abort, jsonify, current_app
from flask_login import current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError

from mergin.sync.tasks import remove_transaction_chunks

from .schemas_v2 import ProjectSchema as ProjectSchemaV2
from ..app import db
from ..auth import auth_required
from ..auth.models import User
from .errors import (
    AnotherUploadRunning,
    BigChunkError,
    DataSyncError,
    ProjectLocked,
    ProjectVersionExists,
    StorageLimitHit,
    UploadError,
)
from .files import ChangesSchema, ProjectFileSchema
from .forms import project_name_validation
from .models import (
    Project,
    ProjectRole,
    ProjectMember,
    ProjectVersion,
    Upload,
    project_version_created,
    push_finished,
)
from .permissions import ProjectPermissions, require_project_by_uuid, projects_query
from .public_api_controller import catch_sync_failure
from .schemas import (
    ProjectMemberSchema,
    UploadChunkSchema,
)
from .storages.disk import move_to_tmp, save_to_file
from .utils import get_device_id, get_ip, get_user_agent, get_chunk_location
from .workspace import WorkspaceRole
from ..utils import parse_order_params


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
    validation_error = project_name_validation(new_name)
    if validation_error:
        return (
            jsonify(code="InvalidProjectName", detail=validation_error),
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
                    name=user.profile.name(),
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


def get_project(id, files_at_version=None):
    """Get project info. Include list of files at specific version if requested."""
    project = require_project_by_uuid(id, ProjectPermissions.Read, expose=False)
    data = ProjectSchemaV2().dump(project)
    if files_at_version:
        pv = ProjectVersion.query.filter_by(
            project_id=project.id, name=ProjectVersion.from_v_name(files_at_version)
        ).first()
        if pv:
            data["files"] = ProjectFileSchema(
                only=("path", "mtime", "size", "checksum"), many=True
            ).dump(pv.files)

    return data, 200


@auth_required
@catch_sync_failure
def create_project_version(id):
    """Create a new project version from pushed data"""
    version: int = ProjectVersion.from_v_name(request.json["version"])
    changes = request.json["changes"]
    project_permission: ProjectPermissions = (
        current_app.project_handler.get_push_permission(changes)
    )
    project = require_project_by_uuid(id, project_permission)
    # pass full project object to request for later use
    request.view_args["project"] = project

    if project.locked_until:
        return ProjectLocked().response(423)

    next_version = project.next_version()
    v_next_version = ProjectVersion.to_v_name(next_version)
    version_dir = os.path.join(project.storage.project_dir, v_next_version)

    pv = project.get_latest_version()
    if pv and pv.name != version:
        return ProjectVersionExists(version, pv.name).response(409)

    # reject push if there is another one already running
    pending_upload = Upload.query.filter_by(project_id=project.id).first()
    if pending_upload and pending_upload.is_active():
        return AnotherUploadRunning().response(409)

    try:
        ChangesSchema().validate(changes)
        upload_changes = ChangesSchema().dump(changes)
    except ValidationError as err:
        msg = err.messages[0] if type(err.messages) == list else "Invalid input data"
        return UploadError(error=msg).response(422)

    to_be_added_files = upload_changes["added"]
    to_be_updated_files = upload_changes["updated"]
    to_be_removed_files = upload_changes["removed"]

    # check consistency of changes
    current_files = set(file.path for file in project.files)
    added_files = set(file["path"] for file in to_be_added_files)
    if added_files and added_files.issubset(current_files):
        return UploadError(
            error=f"Add changes contain files which already exist"
        ).response(422)

    modified_files = set(
        file["path"] for file in to_be_updated_files + to_be_removed_files
    )
    if modified_files and not modified_files.issubset(current_files):
        return UploadError(
            error="Update or remove changes contain files that are not in project"
        ).response(422)

    # Check user data limit
    updated_files = list(
        filter(
            lambda i: i.path in [f["path"] for f in to_be_updated_files],
            project.files,
        )
    )
    additional_disk_usage = (
        sum(file["size"] for file in to_be_added_files + to_be_updated_files)
        - sum(file.size for file in updated_files)
        - sum(file["size"] for file in to_be_removed_files)
    )

    current_usage = project.workspace.disk_usage()
    requested_storage = current_usage + additional_disk_usage
    if requested_storage > project.workspace.storage:
        return StorageLimitHit(current_usage, project.workspace.storage).response(422)

    # we have done all checks but this request is just a dry-run
    if request.json.get("check_only", False):
        return NoContent, 204

    try:
        # while processing data, block other uploads
        upload = Upload(project, version, upload_changes, current_user.id)
        db.session.add(upload)
        # Creating blocking upload can fail, e.g. in case of racing condition
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # check and clean dangling blocking uploads or abort
        for current_upload in project.uploads.all():
            if current_upload.is_active():
                return AnotherUploadRunning().response(409)
            db.session.delete(current_upload)
            db.session.commit()
            # previous push attempt is definitely lost
            project.sync_failed(
                "",
                "push_lost",
                "Push artefact removed by subsequent push",
                current_user.id,
            )

        try:
            # Try again after cleanup
            upload = Upload(project, version, upload_changes, current_user.id)
            db.session.add(upload)
            db.session.commit()
            move_to_tmp(upload.upload_dir)
        except IntegrityError as err:
            logging.error(f"Failed to create upload session: {str(err)}")
            return AnotherUploadRunning().response(409)

    # Create transaction folder and lockfile
    os.makedirs(upload.upload_dir)
    open(upload.lockfile, "w").close()

    file_changes, errors = upload.process_chunks(use_shared_chunk_dir=True)
    # files consistency or geodiff related issues, project push would never succeed, whole upload is aborted
    if errors:
        upload.clear()
        return DataSyncError(failed_files=errors).response(422)

    try:
        pv = ProjectVersion(
            project,
            next_version,
            current_user.id,
            file_changes,
            get_ip(request),
            get_user_agent(request),
            get_device_id(request),
        )
        db.session.add(pv)
        db.session.add(project)
        db.session.commit()

        # let's move uploaded files where they are expected to be
        if to_be_added_files or to_be_updated_files:
            temp_files_dir = os.path.join(upload.upload_dir, "files", v_next_version)
            os.renames(temp_files_dir, version_dir)

            # remove used chunks
            # get chunks from added and updated files
            chunks_ids = []
            for file in to_be_added_files + to_be_updated_files:
                file_chunks = file.get("chunks", [])
                chunks_ids.extend(file_chunks)
            remove_transaction_chunks.delay(chunks_ids)

        logging.info(
            f"Push finished for project: {project.id}, project version: {v_next_version}, upload id: {upload.id}."
        )
        project_version_created.send(pv)
        push_finished.send(pv)
    except (
        psycopg2.Error,
        FileNotFoundError,
        IntegrityError,
        ObjectDeletedError,
    ) as err:
        db.session.rollback()
        logging.exception(
            f"Failed to finish push for project: {project.id}, project version: {v_next_version}, "
            f"upload id: {upload.id}.: {str(err)}"
        )
        if (
            os.path.exists(version_dir)
            and not ProjectVersion.query.filter_by(
                project_id=project.id, name=next_version
            ).count()
        ):
            move_to_tmp(version_dir)
        return UploadError().response(422)
    # catch exception during pg transaction so we can rollback and prevent PendingRollbackError during upload clean up
    except gevent.timeout.Timeout:
        db.session.rollback()
        if (
            os.path.exists(version_dir)
            and not ProjectVersion.query.filter_by(
                project_id=project.id, name=next_version
            ).count()
        ):
            move_to_tmp(version_dir)
        raise
    finally:
        # remove artifacts
        upload.clear()

    result = ProjectSchemaV2().dump(project)
    result["files"] = ProjectFileSchema(
        only=("path", "mtime", "size", "checksum"), many=True
    ).dump(project.files)
    return result, 201


@auth_required
def upload_chunk(id: str):
    """
    Push chunk to chunks location.
    """
    project = require_project_by_uuid(id, ProjectPermissions.Edit)
    if project.locked_until:
        return ProjectLocked().response(423)
    # generate uuid for chunk
    chunk_id = str(uuid.uuid4())
    dest_file = get_chunk_location(chunk_id)
    try:
        # we could have used request.data here, but it could eventually cause OOM issue
        save_to_file(request.stream, dest_file, current_app.config["MAX_CHUNK_SIZE"])
    except IOError:
        return BigChunkError().response(413)
    except Exception as e:
        return UploadError(error="Error saving chunk").response(400)

    # Add valid_until timestamp to the response, remove tzinfo for compatibility with DateTimeWithZ
    valid_until = (
        datetime.now(timezone.utc)
        + timedelta(seconds=current_app.config["UPLOAD_CHUNKS_EXPIRATION"])
    ).replace(tzinfo=None)
    return (
        UploadChunkSchema().dump({"id": chunk_id, "valid_until": valid_until}),
        200,
    )


@auth_required
def list_workspace_projects(workspace_id, page, per_page, order_params=None, q=None):
    """Paginate over workspace projects with optional filtering.

    :param workspace_id: ID of the workspace to list projects from
    :param workspace_id: int
    :param page: page number
    :type page: int
    :param per_page: Number of results per page
    :type per_page: int
    :param order_params: Sorting fields e.g. "name ASC,updated DESC"
    :type order_params: str
    :param q: Filter by name with ilike pattern
    :type q: str

    :rtype: Dict[str: List[Project], str: Integer, str: Integer, str: Integer]
    """
    ws = current_app.ws_handler.get(workspace_id)
    if not (ws and ws.is_active):
        abort(404, "Workspace not found")

    if ws.user_has_permissions(current_user, "read"):
        # regular members can list all projects
        projects = Project.query.filter_by(workspace_id=ws.id).filter(
            Project.removed_at.is_(None)
        )
    elif ws.user_has_permissions(current_user, "guest"):
        # guest can list only explicitly shared projects
        projects = projects_query(
            ProjectPermissions.Read, as_admin=False, public=False
        ).filter(Project.workspace_id == ws.id)
    else:
        abort(403, "You do not have permissions to workspace")

    if q:
        projects = projects.filter(Project.name.ilike(f"%{q}%"))

    if order_params:
        order_by_params = parse_order_params(Project, order_params)
        projects = projects.order_by(*order_by_params)

    result = projects.paginate(page, per_page).items
    total = projects.paginate(page, per_page).total

    data = ProjectSchemaV2(many=True).dump(result)
    return jsonify(projects=data, count=total, page=page, per_page=per_page), 200
