# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import render_template, current_app, abort
from sqlalchemy import event

from .. import db
from ..auth.models import User, UserProfile
from .models import Project, ProjectAccess
from .public_api_controller import project_deleted


def remove_user_references(mapper, connection, user):  # pylint: disable=W0612
    q = (
        Project.access.has(ProjectAccess.owners.contains([user.id]))
        | Project.access.has(ProjectAccess.readers.contains([user.id]))
        | Project.access.has(ProjectAccess.readers.contains([user.id]))
    )
    projects = Project.query.filter(q).all()

    def filter_user(ids):
        return filter(lambda i: i != user.id, ids)

    if projects:
        pa_table = ProjectAccess.__table__
        for p in projects:
            pa = p.access
            connection.execute(
                pa_table.update().where(pa_table.c.project_id == p.id),
                owners=filter_user(pa.owners),
                writers=filter_user(pa.writers),
                readers=filter_user(pa.readers),
            )


def project_post_delete_actions(project: Project) -> None:  # pylint: disable=W0612
    """After project is deleted inform users by sending email"""
    from ..celery import send_email_async

    if not project.access:
        return
    users_ids = list(
        set(project.access.owners + project.access.writers + project.access.readers)
    )
    users_profiles = UserProfile.query.filter(UserProfile.user_id.in_(users_ids)).all()
    project_workspace = project.workspace
    for profile in users_profiles:
        # skip the user who triggered deletion
        if profile.user.username == project.removed_by:
            continue

        if not (profile.receive_notifications and profile.user.verified_email):
            continue

        email_data = {
            "subject": f'Mergin project {"/".join([project_workspace.name, project.name])} has been deleted',
            "html": render_template(
                "email/removed_project.html",
                subject="Project deleted",
                project=project,
                username=profile.user.username,
            ),
            "recipients": [profile.user.email],
            "sender": current_app.config["MAIL_DEFAULT_SENDER"],
        }
        send_email_async.delay(**email_data)


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def register_events():
    event.listen(User, "before_delete", remove_user_references)
    event.listen(db.session, "before_commit", check)
    project_deleted.connect(project_post_delete_actions)


def remove_events():
    event.remove(User, "before_delete", remove_user_references)
    event.remove(db.session, "before_commit", check)
    project_deleted.disconnect(project_post_delete_actions)
