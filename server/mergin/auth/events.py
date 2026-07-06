# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from enum import Enum


class AuthEventType(str, Enum):
    # authentication events
    USER_LOGIN_SUCCEEDED = "user.login.succeeded"
    USER_LOGIN_FAILED = "user.login.failed"
    USER_PASSWORD_CHANGED = "user.password.changed"
    USER_PASSWORD_RESET = "user.password.reset"  # token-based reset (unauthenticated)
    # general CRUD (SQLAlchemy listeners)
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    # lifecycle events (explicit emit only; active/inactive_since excluded from user.updated)
    USER_MARKED_FOR_DELETION = (
        "user.marked_for_deletion"  # user or admin triggers deletion flow
    )
    USER_DEACTIVATED = "user.deactivated"  # admin sets active=False without deletion
    USER_RESTORED = (
        "user.restored"  # admin re-activates after deactivation or marked_for_deletion
    )
    USER_DELETED = "user.deleted"  # personal data permanently erased
