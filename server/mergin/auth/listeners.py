# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from typing import Any

from sqlalchemy import event, inspect as sa_inspect
from sqlalchemy.orm import object_session

from ..audit import emit
from ..audit.listeners import actor_context, field_changes
from .events import AuthEventType
from .models import User

# Fields excluded from user.updated audit events:
#   - sensitive values that must never appear in logs (passwd)
#   - high-frequency operational fields (last_signed_in, registration_date)
#   - lifecycle state fields covered by dedicated events (active, inactive_since)
#   - is_admin covered by the dedicated user.admin_panel_access.changed event
# frozenset prevents accidental mutation of module-level state.
_EXCLUDED_FROM_USER_UPDATED = frozenset(
    {
        "passwd",
        "last_signed_in",
        "registration_date",
        "active",
        "inactive_since",
        "is_admin",
    }
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
    session = object_session(target)
    source = session.info.get("audit_user_creation_source") if session else None
    # For self-registration there is no prior actor — attribute the creation to the new user.
    if not ctx.get("actor_email") and source == "self_registration":
        ctx["actor_email"] = target.email
        ctx["actor_id"] = target.id
    emit(
        AuthEventType.USER_CREATED,
        **ctx,
        target_user_id=target.id,
        target_email=target.email,
        target_username=target.username,
        source=source,
    )
    if target.is_admin:
        emit(
            AuthEventType.USER_ADMIN_PANEL_ACCESS_CHANGED,
            **ctx,
            target_user_id=target.id,
            old_is_admin=None,
            new_is_admin=True,
        )


def _on_user_updated(_mapper, _connection, target):
    if object_session(target).info.get("audit_skip_user_update"):
        return
    changes = field_changes(target, _EXCLUDED_FROM_USER_UPDATED)
    if changes:
        emit(
            AuthEventType.USER_UPDATED,
            **actor_context(),
            target_user_id=target.id,
            target_email=target.email,
            **changes,
        )
    # is_admin is excluded from field_changes; handle it with a dedicated event.
    is_admin_hist = sa_inspect(target).attrs.is_admin.history
    if is_admin_hist.has_changes():
        old = is_admin_hist.deleted[0] if is_admin_hist.deleted else None
        new = is_admin_hist.added[0] if is_admin_hist.added else None
        if old != new:
            emit(
                AuthEventType.USER_ADMIN_PANEL_ACCESS_CHANGED,
                **actor_context(),
                target_user_id=target.id,
                old_is_admin=old,
                new_is_admin=new,
            )


def register_listeners():
    if event.contains(User, "after_insert", _on_user_created):
        return
    event.listen(User, "after_insert", _on_user_created)
    event.listen(User, "after_update", _on_user_updated)
