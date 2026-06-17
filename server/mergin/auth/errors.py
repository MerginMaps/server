# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
from typing import Dict

from ..app import ResponseError


class AccountLockedError(Exception, ResponseError):
    code = "AccountLocked"
    detail = "Account temporarily locked due to too many failed login attempts"

    def __init__(self, locked_until: datetime.datetime):
        self.locked_until = locked_until

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["locked_until"] = self.locked_until.isoformat()
        return data
