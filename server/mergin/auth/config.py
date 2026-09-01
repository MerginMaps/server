# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from decouple import config


class Configuration(object):
    SECURITY_BEARER_SALT = config("SECURITY_BEARER_SALT")
    SECURITY_EMAIL_SALT = config("SECURITY_EMAIL_SALT")
    SECURITY_PASSWORD_SALT = config("SECURITY_PASSWORD_SALT")
    SECURITY_UNLOCK_SALT = config("SECURITY_UNLOCK_SALT")
    BEARER_TOKEN_EXPIRATION = config(
        "BEARER_TOKEN_EXPIRATION", default=3600 * 12, cast=int
    )  # in seconds
    ACCOUNT_EXPIRATION = config("ACCOUNT_EXPIRATION", default=5, cast=int)  # in days
    BCRYPT_LOG_ROUNDS = config("BCRYPT_LOG_ROUNDS", default=12, cast=int)
    # Comma-separated "attempts:seconds" pairs, e.g. "5:300,10:3600"
    LOCKOUT_POLICY = config("LOCKOUT_POLICY", default="5:300,10:3600")
    # trailing window in seconds over which failed login attempts are counted
    LOCKOUT_WINDOW = config("LOCKOUT_WINDOW", default=3600, cast=int)
