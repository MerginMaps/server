# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime

from flask import Flask, current_app

from .events import AuditEvent, EventType
from .sinks import NullSink


def register(app: Flask) -> None:
    """Wire the audit module into a Flask app.

    Sets NullSink as the default.
    """
    app.audit_sink = NullSink()


def emit(
    event_type: EventType,
    actor_id=None,
    actor_email=None,
    actor_user_agent=None,
    actor_device_id=None,
    ip_address=None,
    target_id=None,
    scope_id=None,
    **detail,
) -> None:
    """Emit one audit event to the configured sink.

    target_type is auto-derived from the noun segment of event_type (e.g. "user"
    from "user.login.succeeded"). scope_id is the workspace that owns this event
    (None for global events). Extra keyword arguments become the context dict.
    """
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_email=actor_email,
        actor_user_agent=actor_user_agent,
        actor_device_id=actor_device_id,
        ip_address=ip_address,
        timestamp=datetime.datetime.utcnow(),
        target_id=target_id,
        target_type=event_type.split(".")[0] if event_type else None,
        scope_id=scope_id,
        context=detail,
    )
    current_app.audit_sink.write(event)
