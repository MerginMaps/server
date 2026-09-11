# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any

# Noun.verb dot-notation string, e.g. "user.login.succeeded".
# Each module defines its own str enum; the sink stores the raw string.
EventType = str


@dataclass(frozen=True)
class AuditEvent:
    event_type: EventType
    actor_ip: str | None
    happened_at: datetime.datetime
    actor_id: int | None
    actor_email: str | None
    actor_ua: str | None
    actor_device: str | None  # X-Device-Id header; set by mobile/QGIS clients
    target_user_id: int | None  # set when the target is a user
    target_project_id: uuid.UUID | None  # set when the target is a project
    target_workspace_id: (
        int | None
    )  # workspace the event belongs to; set for project and workspace events
    metadata: dict[str, Any] = field(default_factory=dict)
