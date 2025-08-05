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


class ProjectLocked(ResponseError):
    code = "ProjectLocked"
    detail = "The project is currently locked and you cannot make changes to it"


class DataSyncError(ResponseError):
    code = "DataSyncError"
    detail = "There are either corrupted files or it is not possible to create version with provided geopackage data"

    def __init__(self, failed_files: Dict):
        self.failed_files = failed_files

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["failed_files"] = self.failed_files
        return data


class ProjectVersionMismatch(ResponseError):
    code = "ProjectVersionMismatch"
    detail = "Project version mismatch"

    def __init__(self, client_version: int, server_version: int):
        self.client_version = client_version
        self.server_version = server_version

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["client_version"] = f"v{self.client_version}"
        data["server_version"] = f"v{self.server_version}"
        return data


class UploadError(ResponseError):
    code = "UploadError"
    detail = "Project version could not be created"

    def __init__(self, error: str = None):
        self.error = error

    def to_dict(self) -> Dict:
        data = super().to_dict()
        if self.error is not None:
            data["detail"] = self.error + f" ({self.code})"
        return data
