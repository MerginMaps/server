# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event

from ..app import db
from .models import ProjectVersion
from .public_api_controller import push_finished
from .tasks import remove_stale_project_uploads


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def cleanup_on_push_finished(project_version: ProjectVersion) -> None:
    """On finished push trigger celery job cleanup"""
    remove_stale_project_uploads.delay(project_version.project_id)


def register_events():
    event.listen(db.session, "before_commit", check)
    push_finished.connect(cleanup_on_push_finished)


def remove_events():
    event.remove(db.session, "before_commit", check)
    push_finished.connect(cleanup_on_push_finished)
