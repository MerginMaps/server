# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime

from connexion import NoContent, request
from flask import abort, jsonify
from flask_login import current_user

from mergin import db
from mergin.auth import auth_required
from mergin.sync.models import Project
from mergin.sync.permissions import ProjectPermissions, require_project_by_uuid
from mergin.sync.utils import is_name_allowed


@auth_required
def schedule_delete_project(id_):
    """Schedule deletion of the project.
    Celery job `mergin.sync.tasks.remove_projects_backups` does the
    rest.

    :param id_: Project id
    :type id_: str
    """
    project = require_project_by_uuid(id_, ProjectPermissions.Delete)
    project.removed_at = datetime.utcnow()
    project.removed_by = current_user.username
    db.session.commit()

    return NoContent, 204


@auth_required
def delete_project_now(id_):
    """Delete the project immediately.

    :param id_: Project id
    :type id_: str
    """
    project = require_project_by_uuid(id_, ProjectPermissions.Delete, scheduled=True)
    project.delete()

    return NoContent, 204


@auth_required
def update_project(id_):
    """Rename project

    :param id_: Project_id
    :type id_: str
    """
    project = require_project_by_uuid(id_, ProjectPermissions.Update)
    new_name = request.json["name"]

    if not is_name_allowed(new_name):
        return (
            jsonify(
                code="InvalidProjectName", detail="Entered project name is invalid"
            ),
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
