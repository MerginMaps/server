# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime, timedelta
from sqlalchemy.sql.operators import isnot

from ..celery import celery
from ..app import db
from .models import User
from .config import Configuration


@celery.task
def anonymize_removed_users():
    """Permanently 'delete' users marked for removal by removing personal information"""
    db.session.info["msg"] = "anonymize_removed_users"
    before_expiration = datetime.today() - timedelta(Configuration.ACCOUNT_EXPIRATION)
    users = User.query.filter(
        isnot(User.active, True),
        User.inactive_since <= before_expiration,
        User.username.op("~")("^(?!deleted_\d{13})"),
    ).all()
    for user in users:
        user.anonymize()
