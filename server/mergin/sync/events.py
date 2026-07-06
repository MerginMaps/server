# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from enum import Enum


class SyncEventType(str, Enum):
    # automatic CRUD events (SQLAlchemy listeners)
    PROJECT_CREATED = "project.created"  # also emitted on clone
    PROJECT_UPDATED = "project.updated"
    # lifecycle events (explicit emit)
    PROJECT_MARKED_FOR_DELETION = "project.marked_for_deletion"
    PROJECT_RESTORED = "project.restored"
    PROJECT_DELETED = "project.deleted"
    # membership events (explicit emit)
    PROJECT_MEMBER_ADDED = "project.member.added"
    PROJECT_MEMBER_UPDATED = "project.member.updated"
    PROJECT_MEMBER_DELETED = "project.member.deleted"
    # access request events (explicit emit)
    PROJECT_ACCESS_REQUEST_CREATED = "project.access_request.created"
    PROJECT_ACCESS_REQUEST_ACCEPTED = "project.access_request.accepted"
    PROJECT_ACCESS_REQUEST_REJECTED = "project.access_request.rejected"
    # data events (explicit emit)
    PROJECT_VERSION_CREATED = "project.version.created"
