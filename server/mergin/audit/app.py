# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
import logging

from flask import Flask, current_app, has_app_context

from .events import AuditEvent, EventType
from .sinks import NullSink

logger = logging.getLogger(__name__)


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
    target_user_id=None,
    target_project_id=None,
    target_workspace_id=None,
    **metadata,
) -> None:
    """Emit one audit event to the configured sink.

    Set at least one of target_user_id, target_project_id, target_workspace_id to identify the target.
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
        target_user_id=target_user_id,
        target_project_id=target_project_id,
        target_workspace_id=target_workspace_id,
        metadata=metadata,
    )
    if not has_app_context() or "audit" not in current_app.extensions:
        return
    try:
        current_app.extensions["audit"]["sink"].write(event)
    except Exception:
        logger.warning("Failed to emit audit event %s", event_type, exc_info=True)
