# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event

from .models import ProjectVersion
from .tasks import optimize_storage
from ..app import db


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def optimize_gpgk_storage(mapper, connection, project_version):
    # do not optimize on every version, every 10th is just fine
    if not project_version.name % 10:
        optimize_storage.delay(project_version.project_id)


def register_events():
    event.listen(db.session, "before_commit", check)
    event.listen(ProjectVersion, "after_insert", optimize_gpgk_storage)


def remove_events():
    event.remove(db.session, "before_commit", check)
    event.listen(ProjectVersion, "after_insert", optimize_gpgk_storage)
