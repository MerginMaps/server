# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime

from flask import Flask, current_app

from .events import AuditEvent, EventType
from .sinks import NullSink


def register(app: Flask) -> None:
    """Wire the audit module into a Flask app.

    Stores the sink in app.extensions["audit"] so emit() has one consistent lookup path.
    """
    app.extensions["audit"] = {"sink": NullSink()}


def emit(
    event_type: EventType,
    actor_id=None,
    actor_email=None,
    actor_ua=None,
    actor_device=None,
    actor_ip=None,
    user_id=None,
    project_id=None,
    workspace_id=None,
    **metadata,
) -> None:
    """Emit one audit event to the configured sink.

    Set at least one of user_id, project_id, workspace_id to identify the target.
    Extra keyword arguments become the metadata dict.
    """
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_email=actor_email,
        actor_ua=actor_ua,
        actor_device=actor_device,
        actor_ip=actor_ip,
        happened_at=datetime.datetime.utcnow(),
        user_id=user_id,
        project_id=project_id,
        workspace_id=workspace_id,
        metadata=metadata,
    )
    current_app.extensions["audit"]["sink"].write(event)
