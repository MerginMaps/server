# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from decouple import config


class Configuration(object):
    SECURITY_PASSWORD_SALT = config("SECURITY_PASSWORD_SALT")
    BEARER_TOKEN_EXPIRATION = config(
        "BEARER_TOKEN_EXPIRATION", default=3600 * 12, cast=int
    )  # in seconds
    ACCOUNT_EXPIRATION = config("ACCOUNT_EXPIRATION", default=5, cast=int)  # in days
