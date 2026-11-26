# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from ..app import ResponseError


class TokenExpired(ResponseError):
    code = "TokenExpired"
    detail = "Your session has expired, please log in again"


class TokenRevoked(ResponseError):
    code = "TokenRevoked"
    detail = "Your session is no longer valid, please log in again"


class TokenInvalid(ResponseError):
    code = "TokenInvalid"
    detail = "Invalid authentication token"
