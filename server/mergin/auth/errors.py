# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from ..app import ResponseError


class AccountLockedError(Exception, ResponseError):
    code = "AccountLocked"
    detail = "Account temporarily locked due to too many failed login attempts"
