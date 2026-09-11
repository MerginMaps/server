# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""
Utilities for writing SQLAlchemy-based audit listeners in any module.
"""

import logging
from contextlib import contextmanager

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import ColumnProperty
from flask import has_request_context, request, current_app
from flask_login import current_user

from ..utils import get_ip, get_user_agent, get_device_id
from .app import emit

logger = logging.getLogger(__name__)


@contextmanager
def audit_session_flags(session, **flags):
    """Context manager that sets db.session.info flags for the duration of a block
    and removes them in a finally clause so they never leak on exceptions."""
    session.info.update(flags)
    try:
        yield
    finally:
        for key in flags:
            session.info.pop(key, None)


def request_context():
    """Return the three request-derived actor kwargs: user_agent, device_id, ip.

    Use **request_context() in explicit emit() calls so adding a new request
    field only requires changing this one function.
    """
    if not has_request_context():
        return dict(actor_ua=None, actor_device=None, actor_ip=None)
    return dict(
        actor_ua=get_user_agent(request),
        actor_device=get_device_id(request),
        actor_ip=get_ip(request),
    )


def actor_context():
    """Return full actor kwargs for emit() drawn from the current request context.

    Used by SQLAlchemy listeners where current_user is the actor.
    """
    actor_id = None
    actor_email = None
    if has_request_context() and hasattr(
        current_app._get_current_object(), "login_manager"
    ):
        try:
            if current_user.is_authenticated:
                actor_id = current_user.id
                actor_email = current_user.email
        except Exception:
            pass
    return dict(actor_id=actor_id, actor_email=actor_email, **request_context())


def field_changes(target, skip=frozenset()):
    """Return flat old_<field>/new_<field> context for all changed non-skipped column fields.

    Only column attributes are included — relationships are skipped because their
    history entries are ORM instances, not JSON-serializable values.
    """
    mapper = sa_inspect(type(target))
    ctx = {}
    for attr in sa_inspect(target).attrs:
        if attr.key in skip:
            continue
        if not isinstance(mapper.attrs[attr.key], ColumnProperty):
            continue
        hist = attr.history
        if hist.has_changes():
            old = hist.deleted[0] if hist.deleted else None
            new = hist.added[0] if hist.added else None
            if old != new:
                ctx[f"old_{attr.key}"] = old
                ctx[f"new_{attr.key}"] = new
    return ctx
