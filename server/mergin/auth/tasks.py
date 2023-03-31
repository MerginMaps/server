# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime, timedelta
from sqlalchemy.sql.operators import isnot

from ..celery import celery
from .. import db
from .models import User
from .config import Configuration


@celery.task
def prune_removed_users():
    """Permanently delete users marked for removal"""
    db.session.info = {"msg": "prune_removed_users"}
    before_expiration = datetime.today() - timedelta(Configuration.ACCOUNT_EXPIRATION)
    users = (
        db.session.query(User.id)
        .filter(isnot(User.active, True), User.inactive_since <= before_expiration)
        .all()
    )
    users_ids = [u.id for u in users]

    db.session.execute(User.__table__.delete().where(User.id.in_(users_ids)))
    db.session.commit()
