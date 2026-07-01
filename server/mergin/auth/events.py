# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from enum import Enum


class AuthEventType(str, Enum):
    # explicit auth action events
    USER_LOGIN_SUCCEEDED = "user.login.succeeded"
    USER_LOGIN_FAILED = "user.login.failed"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_CHANGED = "user.password.changed"
    USER_PASSWORD_RESET = "user.password.reset"  # token-based reset (unauthenticated)
    # automatic CRUD events (SQLAlchemy listeners)
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    # lifecycle events (explicit emit)
    USER_CLOSED = "user.closed"
    USER_ANONYMIZED = "user.anonymized"
