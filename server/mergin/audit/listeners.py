# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""
Utilities for writing SQLAlchemy-based audit listeners in any module.
"""

import logging

from sqlalchemy import inspect as sa_inspect
from flask import has_request_context, has_app_context, request, current_app
from flask_login import current_user

from ..utils import get_ip, get_user_agent, get_device_id
from .app import emit

logger = logging.getLogger(__name__)


def request_context():
    """Return the three request-derived actor kwargs: user_agent, device_id, ip.

    Use **request_context() in explicit emit() calls so adding a new request
    field only requires changing this one function.
    """
    if not has_request_context():
        return dict(actor_user_agent=None, actor_device_id=None, ip_address=None)
    return dict(
        actor_user_agent=get_user_agent(request),
        actor_device_id=get_device_id(request),
        ip_address=get_ip(request),
    )


def actor_context():
    """Return full actor kwargs for emit() drawn from the current request context.

    Used by SQLAlchemy listeners where current_user is the actor.
    """
    actor_id = None
    actor_email = None
    if has_request_context() and current_user.is_authenticated:
        actor_id = current_user.id
        actor_email = current_user.email
    return dict(actor_id=actor_id, actor_email=actor_email, **request_context())


def field_changes(target, skip=frozenset()):
    """Return flat old_<field>/new_<field> context for all changed non-skipped fields."""
    ctx = {}
    for attr in sa_inspect(target).attrs:
        if attr.key in skip:
            continue
        hist = attr.history
        if hist.has_changes():
            old = hist.deleted[0] if hist.deleted else None
            new = hist.added[0] if hist.added else None
            if old != new:
                ctx[f"old_{attr.key}"] = old
                ctx[f"new_{attr.key}"] = new
    return ctx


def emit_safe(event_type, **kwargs):
    """Emit without raising if outside app context or sink not yet configured.

    Works both inside HTTP requests (actor context populated) and Celery tasks
    (actor fields are None, indicating a system-initiated action).
    """
    if not has_app_context() or not hasattr(current_app, "audit_sink"):
        return
    try:
        emit(event_type, **kwargs)
    except Exception:
        logger.warning("Failed to emit audit event %s", event_type, exc_info=True)
