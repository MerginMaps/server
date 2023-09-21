# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime

from connexion import NoContent
from flask import abort
from flask_login import current_user

from mergin import db
from mergin.auth import auth_required
from mergin.sync.models import Project
from mergin.sync.permissions import ProjectPermissions, require_project_by_uuid


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
    db.session.delete(project)
    db.session.commit()

    return NoContent, 204
