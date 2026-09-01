# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event

from .events import SyncEventType
from .models import ProjectUser, ProjectVersion
from .tasks import optimize_storage
from ..app import db
from ..audit import emit
from ..audit.listeners import actor_context


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def optimize_gpgk_storage(mapper, connection, project_version):
    # do not optimize on every version, every 10th is just fine
    if not project_version.name % 10:
        optimize_storage.delay(project_version.project_id)


def on_project_member_deleted(mapper, connection, project_user: ProjectUser):
    """Emit PROJECT_MEMBER_DELETED whenever a ProjectUser row is deleted via the ORM."""
    if db.session.info.get("suppress_project_member_deleted"):
        return

    from .models import Project

    project = db.session.get(Project, project_user.project_id)
    workspace = project.workspace if project else None
    ws_name = workspace.name if workspace else None
    reason = db.session.info.get("project_member_delete_reason", "removed")
    emit(
        SyncEventType.PROJECT_MEMBER_DELETED,
        **actor_context(),
        target_project_id=project_user.project_id,
        target_workspace_id=project.workspace_id if project else None,
        target_user_id=project_user.user_id,
        target_email=project_user.user.email if project_user.user else None,
        workspace_name=ws_name,
        project_name=f"{ws_name}/{project.name}" if ws_name and project else None,
        role=project_user.role,
        reason=reason,
    )


def register_events():
    event.listen(db.session, "before_commit", check)
    event.listen(ProjectVersion, "after_insert", optimize_gpgk_storage)
    event.listen(ProjectUser, "after_delete", on_project_member_deleted)


def remove_events():
    event.remove(db.session, "before_commit", check)
    event.remove(ProjectVersion, "after_insert", optimize_gpgk_storage)
    event.remove(ProjectUser, "after_delete", on_project_member_deleted)
