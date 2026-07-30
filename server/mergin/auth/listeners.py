# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from typing import Any

from flask import has_request_context
from sqlalchemy import event
from sqlalchemy.orm import object_session

from ..audit.listeners import actor_context, field_changes, emit_safe
from .events import AuthEventType
from .models import User

# Fields excluded from user.updated audit events:
#   - sensitive values that must never appear in logs (passwd)
#   - high-frequency operational fields (last_signed_in, registration_date)
#   - lifecycle state fields covered by dedicated events (active, inactive_since)
# frozenset prevents accidental mutation of module-level state.
_SKIP = frozenset(
    {"passwd", "last_signed_in", "registration_date", "active", "inactive_since"}
)


def _on_user_created(_mapper: Any, _connection: Any, target: User) -> None:
    """Emit USER_CREATED after a User row is inserted.

    Actor attribution:
    - Authenticated request (admin creates user): actor comes from actor_context().
    - Unauthenticated request (self-registration): no session yet, so the new user
      themselves is used as the actor rather than leaving it null.
    - No request context (Celery/system import): actor stays null to signal a system action.
    """
    ctx = actor_context()
    if not ctx.get("actor_email") and has_request_context():
        ctx["actor_email"] = target.email
        ctx["actor_id"] = target.id
    emit_safe(
        AuthEventType.USER_CREATED,
        **ctx,
        user_id=target.id,
        target_email=target.email,
    )


def _on_user_updated(_mapper, _connection, target):
    if object_session(target).info.get("audit_skip_user_update"):
        return
    changes = field_changes(target, _SKIP)
    if not changes:
        return
    emit_safe(
        AuthEventType.USER_UPDATED,
        **actor_context(),
        user_id=target.id,
        target_email=target.email,
        **changes,
    )


def register_listeners():
    if event.contains(User, "after_insert", _on_user_created):
        return
    event.listen(User, "after_insert", _on_user_created)
    event.listen(User, "after_update", _on_user_updated)
