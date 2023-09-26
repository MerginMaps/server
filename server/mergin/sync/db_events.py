# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event

from .. import db
from ..auth.models import User
from .models import Project, ProjectAccess


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


def remove_project_storage(mapper, connection, project):
    project.storage.delete()


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def register_events():
    event.listen(User, "before_delete", remove_user_references)
    event.listen(Project, "before_delete", remove_project_storage)
    event.listen(db.session, "before_commit", check)


def remove_events():
    event.remove(User, "before_delete", remove_user_references)
    event.remove(Project, "before_delete", remove_project_storage)
    event.remove(db.session, "before_commit", check)
