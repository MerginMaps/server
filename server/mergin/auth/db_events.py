# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from .app import force_delete_user
from .. import db
from ..auth.models import User


def permanently_delete_user(user: User):
    """Permanently remove user from database"""
    db.session.delete(user)
    db.session.commit()


def register_events():
    force_delete_user.connect(permanently_delete_user)


def remove_events():
    force_delete_user.disconnect(permanently_delete_user)
