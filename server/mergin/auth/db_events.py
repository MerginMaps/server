# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from flask import render_template, current_app
from sqlalchemy import event

from .app import force_delete_user
from .. import db
from ..auth.models import UserProfile, User


def before_user_profile_updated(mapper, connection, target):
    """Before profile updated, inform user by sending email about that profile that changed
    Just send email if user want to receive notifications
    """
    from ..celery import send_email_async

    if target.receive_notifications and target.user.verified_email:
        state = db.inspect(target)
        changes = {}

        for attr in state.attrs:
            hist = attr.load_history()
            if not hist.has_changes():
                continue

            before = hist.deleted[0]
            after = hist.added[0]
            field = attr.key

            # if boolean, show Yes or No
            if before is not None and isinstance(before, bool):
                before = "Yes" if before is True else "No"
            if after is not None and isinstance(after, bool):
                after = "Yes" if after is True else "No"

            profile_key = field.title().replace("_", " ")
            changes[profile_key] = {"before": before, "after": after}

        # inform user
        if changes:
            email_data = {
                "subject": "Profile has been changed",
                "html": render_template(
                    "email/profile_changed.html",
                    subject="Profile update",
                    user=target.user,
                    changes=changes,
                ),
                "recipients": [target.user.email],
                "sender": current_app.config["MAIL_DEFAULT_SENDER"],
            }
            send_email_async.delay(**email_data)


def permanently_delete_user(user: User):
    """Permanently remove user from database"""
    db.session.delete(user)
    db.session.commit()


def register_events():
    event.listen(UserProfile, "after_update", before_user_profile_updated)
    force_delete_user.connect(permanently_delete_user)


def remove_events():
    event.remove(UserProfile, "after_update", before_user_profile_updated)
    force_delete_user.disconnect(permanently_delete_user)
