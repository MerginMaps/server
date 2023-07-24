# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from typing import List, Dict
from ..app import ResponseError


class UpdateProjectAccessError(ResponseError):
    code = "UpdateProjectAccessError"
    detail = "Project access could not be updated"

    def __init__(self, invalid_usernames: List[str], invalid_ids: List[int]):
        self.invalid_usernames = invalid_usernames
        self.invalid_ids = invalid_ids

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["invalid_usernames"] = self.invalid_usernames
        data["invalid_ids"] = self.invalid_ids
        return data


class StorageLimitHit(ResponseError):
    code = "StorageLimitHit"
    detail = "You have reached a data limit"

    def __init__(self, current_usage: int, storage_limit: int):
        self.current_usage = current_usage
        self.storage_limit = storage_limit

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["current_usage"] = self.current_usage
        data["storage_limit"] = self.storage_limit
        return data
