# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Noun.verb dot-notation string, e.g. "user.login.succeeded".
# Each module defines its own str enum; the sink stores the raw string.
EventType = str


@dataclass(frozen=True)
class AuditEvent:
    event_type: EventType
    actor_id: Optional[int]
    actor_email: Optional[str]
    actor_user_agent: Optional[str]
    actor_device_id: Optional[str]  # X-Device-Id header; set by mobile/QGIS clients
    ip_address: Optional[str]
    timestamp: datetime.datetime
    target_id: Optional[str]  # primary entity ID, e.g. str(user.id) or str(project.id)
    target_type: Optional[str]  # noun from event_type, e.g. "user" or "project"
    scope_id: Optional[int]  # workspace-level access boundary; None for global events
    context: Dict[str, Any] = field(default_factory=dict)
