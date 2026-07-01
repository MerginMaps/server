# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from enum import Enum


class SyncEventType(str, Enum):
    # automatic CRUD events (SQLAlchemy listeners)
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    # lifecycle events (explicit emit)
    PROJECT_REMOVED = "project.removed"
    PROJECT_DELETED = "project.deleted"
    # lifecycle events (explicit emit)
    PROJECT_RESTORED = "project.restored"
    # access control events (explicit emit)
    PROJECT_ACCESS_GRANTED = "project.access.granted"
    PROJECT_ACCESS_UPDATED = "project.access.updated"
    PROJECT_ACCESS_REVOKED = "project.access.revoked"
    PROJECT_ACCESS_REQUEST_ACCEPTED = "project.access.request.accepted"
    PROJECT_ACCESS_REQUEST_DECLINED = "project.access.request.declined"
    # data events (explicit emit)
    PROJECT_VERSION_CREATED = "project.version.created"
    # explicit action events
    PROJECT_FILE_UPLOADED = "project.file.uploaded"
    PROJECT_FILE_DOWNLOADED = "project.file.downloaded"
