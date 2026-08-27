# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from sqlalchemy import event
from sqlalchemy.orm import object_session

from ..audit import emit
from ..audit.listeners import actor_context, field_changes
from .events import SyncEventType
from .models import Project

# Fields excluded from project.updated audit events — either auto-computed on every
# version push (disk_usage, latest_version, tags), operational metadata (updated,
# storage_params, locked_until), or covered by dedicated events with their own emit
# (removed_at/removed_by are suppressed via audit_skip_project_update instead).
# frozenset prevents accidental mutation of module-level state.
_EXCLUDED_FROM_PROJECT_UPDATED = frozenset(
    {
        "disk_usage",
        "latest_version",
        "updated",
        "storage_params",
        "tags",
    }
)


def _on_project_created(_mapper, _connection, target):
    if object_session(target).info.get("audit_skip_project_create"):
        return
    emit(
        SyncEventType.PROJECT_CREATED,
        **actor_context(),
        target_project_id=target.id,
        target_workspace_id=target.workspace_id,
        project_name=f"{target.workspace.name}/{target.name}",
        workspace_name=target.workspace.name,
        is_public=target.public,
        creator=target.creator_id,
    )


def _on_project_updated(_mapper, _connection, target):
    if object_session(target).info.get("audit_skip_project_update"):
        return
    changes = field_changes(target, _EXCLUDED_FROM_PROJECT_UPDATED)
    if not changes:
        return
    emit(
        SyncEventType.PROJECT_UPDATED,
        **actor_context(),
        target_project_id=target.id,
        target_workspace_id=target.workspace_id,
        project_name=f"{target.workspace.name}/{target.name}",
        **changes,
    )


def register_listeners():
    if event.contains(Project, "after_insert", _on_project_created):
        return
    event.listen(Project, "after_insert", _on_project_created)
    event.listen(Project, "after_update", _on_project_updated)
