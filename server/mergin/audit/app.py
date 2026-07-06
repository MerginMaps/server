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
    user_id=None,
    project_id=None,
    workspace_id=None,
    **detail,
) -> None:
    """Emit one audit event to the configured sink.

    Set at least one of user_id, project_id, workspace_id to identify the target.
    Extra keyword arguments become the context dict.
    """
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_email=actor_email,
        actor_user_agent=actor_user_agent,
        actor_device_id=actor_device_id,
        ip_address=ip_address,
        happened_at=datetime.datetime.utcnow(),
        user_id=user_id,
        project_id=project_id,
        workspace_id=workspace_id,
        context=detail,
    )
    current_app.audit_sink.write(event)
