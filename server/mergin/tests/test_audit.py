# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
from flask import url_for

from ..app import db
from ..auth.events import AuthEventType
from ..auth.models import User
from ..sync.events import SyncEventType
from . import json_headers, DEFAULT_USER, test_workspace_id
from .utils import add_user, create_project, create_workspace, login


def test_login_succeeded_emits_event(client, audit_capture):
    """Successful login via the session endpoint emits USER_LOGIN_SUCCEEDED with actor context."""
    login(client, DEFAULT_USER[0], DEFAULT_USER[1])

    events = audit_capture.of_type(AuthEventType.USER_LOGIN_SUCCEEDED)
    assert len(events) == 1
    e = events[0]
    assert e.actor_email == f"{DEFAULT_USER[0]}@mergin.com"
    assert e.ip_address is not None


def test_login_failed_emits_event_with_login_in_context(client, audit_capture):
    """Failed login emits USER_LOGIN_FAILED and records the attempted login name in context."""
    client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": "mergin", "password": "wrongpassword"}),
        headers=json_headers,
    )

    events = audit_capture.of_type(AuthEventType.USER_LOGIN_FAILED)
    assert len(events) == 1
    e = events[0]
    assert e.context["login"] == "mergin"
    assert e.actor_id is None  # unauthenticated — no actor resolved


def test_user_created_listener_fires(audit_capture):
    """SQLAlchemy after_insert listener emits USER_CREATED when a new user is committed."""
    user = add_user(username="newuser", password="password123")
    user_id = user.id

    events = audit_capture.of_type(AuthEventType.USER_CREATED)
    assert len(events) == 1
    e = events[0]
    assert e.context["target_email"] == "newuser@mergin.com"
    assert e.target_id == str(user_id)
    assert e.target_type == "user"


def test_user_updated_listener_captures_field_changes(audit_capture):
    """after_update listener emits USER_UPDATED with old/new values for changed fields,
    and skips fields in the _SKIP set (e.g. passwd)."""
    user = add_user(username="editme", password="pass1")
    db.session.refresh(user)  # load attributes so history captures old values
    user.email = "changed@mergin.com"
    user.passwd = "newpassword"  # should be skipped
    db.session.commit()

    events = audit_capture.of_type(AuthEventType.USER_UPDATED)
    assert len(events) == 1
    ctx = events[0].context
    assert ctx["new_email"] == "changed@mergin.com"
    assert ctx["old_email"] == "editme@mergin.com"
    assert "new_passwd" not in ctx  # passwd is in _SKIP
    assert "old_passwd" not in ctx


def test_project_created_listener_fires(audit_capture):
    """SQLAlchemy after_insert listener emits PROJECT_CREATED when a project is committed."""
    user = add_user(username="projowner", password="pass123")
    ws = create_workspace()
    project = create_project("myproject", ws, user)
    project_id = project.id

    events = audit_capture.of_type(SyncEventType.PROJECT_CREATED)
    assert len(events) == 1
    e = events[0]
    assert e.context["project_name"] == "myproject"
    assert e.scope_id == test_workspace_id
    assert e.target_id == str(project_id)
    assert e.target_type == "project"


def test_listener_emits_with_null_actor_outside_request(audit_capture):
    """Listeners fire from Celery-like contexts (no request) with actor fields null,
    indicating a system-initiated action rather than a user action."""
    add_user(username="systemcreated", password="pass123")

    events = audit_capture.of_type(AuthEventType.USER_CREATED)
    assert len(events) == 1
    e = events[0]
    assert e.actor_id is None
    assert e.actor_email is None
    assert e.ip_address is None
