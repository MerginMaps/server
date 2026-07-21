# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Noun.verb dot-notation string, e.g. "user.login.succeeded".
# Each module defines its own str enum; the sink stores the raw string.
EventType = str


@dataclass(frozen=True)
class AuditEvent:
    event_type: EventType
    actor_ip: Optional[str]
    happened_at: datetime.datetime
    actor_id: Optional[int]
    actor_email: Optional[str]
    actor_ua: Optional[str]
    actor_device: Optional[str]  # X-Device-Id header; set by mobile/QGIS clients
    user_id: Optional[int]  # set when the target is a user
    project_id: Optional[uuid.UUID]  # set when the target is a project
    workspace_id: Optional[
        int
    ]  # workspace the event belongs to; set for project and workspace events
    metadata: Dict[str, Any] = field(default_factory=dict)
