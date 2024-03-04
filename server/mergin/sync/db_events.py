# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event

from .. import db


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def register_events():
    event.listen(db.session, "before_commit", check)


def remove_events():
    event.remove(db.session, "before_commit", check)
