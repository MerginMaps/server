# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Contract tests: one test per defined EventType to verify the event is emitted
with the required fields.  Each test exercises the minimum code path needed to
trigger the event — it is not a functional test of that path."""

from ..app import db
from ..auth.app import generate_confirmation_token
from ..auth.events import AuthEventType
from ..auth.models import User
from ..sync.events import SyncEventType
from ..sync.models import AccessRequest, Project, ProjectRole
from . import DEFAULT_USER, test_project, test_workspace_id
from .utils import add_user, create_project, create_workspace, login


# ---------------------------------------------------------------------------
# Auth events
# ---------------------------------------------------------------------------


def test_user_login_succeeded(client, audit_capture):
    login(client, DEFAULT_USER[0], DEFAULT_USER[1])

    e = audit_capture.one(AuthEventType.USER_LOGIN_SUCCEEDED)
    assert e.actor_email == f"{DEFAULT_USER[0]}@mergin.com"
    assert e.user_id == e.actor_id  # actor and target are the same person on login


def test_user_login_failed_invalid_credentials(client, audit_capture):
    client.post(
        "/app/auth/login", json={"login": "mergin", "password": "wrongpassword"}
    )

    e = audit_capture.one(AuthEventType.USER_LOGIN_FAILED)
    assert e.metadata["reason"] == "invalid_credentials"
    assert e.metadata["login"] == "mergin"
    assert e.actor_id is None


def test_user_login_failed_account_inactive(client, audit_capture):
    user = add_user("inactive_user", "pass123")
    user.active = False
    db.session.commit()

    client.post(
        "/app/auth/login", json={"login": "inactive_user", "password": "pass123"}
    )

    assert (
        audit_capture.one(AuthEventType.USER_LOGIN_FAILED).metadata["reason"]
        == "account_inactive"
    )


def test_user_password_changed(client, audit_capture):
    user = add_user("pwduser", "oldpass123")
    login(client, "pwduser", "oldpass123")

    client.post(
        "/app/auth/change-password",
        json={
            "old_password": "oldpass123",
            "password": "New#pass456",
            "confirm": "New#pass456",
        },
    )

    e = audit_capture.one(AuthEventType.USER_PASSWORD_CHANGED)
    assert e.user_id == user.id
    assert e.actor_id == user.id


def test_user_password_reset(app, client, audit_capture):
    user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    token = generate_confirmation_token(
        app, user.email, app.config["SECURITY_PASSWORD_SALT"]
    )

    client.post(
        f"/app/auth/reset-password/{token}",
        json={"password": "NewPass#123", "confirm": "NewPass#123"},
    )

    e = audit_capture.one(AuthEventType.USER_PASSWORD_RESET)
    assert e.user_id == user.id
    assert e.metadata["target_email"] == user.email


def test_user_created(audit_capture):
    user = add_user("newuser", "pass123")

    e = audit_capture.one(AuthEventType.USER_CREATED)
    assert e.user_id == user.id
    assert e.metadata["target_email"] == "newuser@mergin.com"


def test_user_updated(audit_capture):
    user = add_user("editme", "pass123")
    db.session.refresh(user)
    user.email = "updated@mergin.com"
    user.passwd = "newpassword"  # in _SKIP — must never appear in audit
    db.session.commit()

    e = audit_capture.one(AuthEventType.USER_UPDATED)
    assert e.metadata["new_email"] == "updated@mergin.com"
    assert e.metadata["old_email"] == "editme@mergin.com"
    assert "new_passwd" not in e.metadata
    assert "old_passwd" not in e.metadata


def test_listener_null_actor_outside_request(audit_capture):
    """Listeners fired from a Celery-like context (no active request) emit null actor
    fields — the event is recorded as a system action with no user attributed."""
    add_user(username="systemcreated", password="pass123")

    e = audit_capture.one(AuthEventType.USER_CREATED)
    assert e.actor_id is None
    assert e.actor_email is None
    assert e.actor_ip is None


def test_user_marked_for_deletion_by_user(client, audit_capture):
    user = add_user("selfdelete", "pass123")
    login(client, "selfdelete", "pass123")

    client.delete("/v1/user")

    e = audit_capture.one(AuthEventType.USER_MARKED_FOR_DELETION)
    assert e.user_id == user.id
    assert e.actor_id == user.id


def test_user_marked_for_deletion_by_admin(client, audit_capture):
    user = add_user("admindelete", "pass123")

    client.delete(f"/app/admin/user/{user.username}")

    assert audit_capture.one(AuthEventType.USER_MARKED_FOR_DELETION).user_id == user.id


def test_user_deactivated(client, audit_capture):
    user = add_user("todeactivate", "pass123")

    client.patch(f"/app/admin/user/{user.username}", json={"active": False})

    assert audit_capture.one(AuthEventType.USER_DEACTIVATED).user_id == user.id


def test_user_restored(client, audit_capture):
    user = add_user("torestore", "pass123")
    user.active = False
    db.session.commit()

    client.patch(f"/app/admin/user/{user.username}", json={"active": True})

    assert audit_capture.one(AuthEventType.USER_RESTORED).user_id == user.id


def test_user_deleted(client, audit_capture):
    user = add_user("todelete", "pass123")

    client.delete(f"/app/admin/user/{user.username}")

    e = audit_capture.one(AuthEventType.USER_DELETED)
    assert e.user_id == user.id
    assert e.metadata["target_email"] == "todelete@mergin.com"


# ---------------------------------------------------------------------------
# Sync / project events
# ---------------------------------------------------------------------------


def test_project_created(audit_capture):
    user = add_user("projowner", "pass123")
    ws = create_workspace()
    project = create_project("myproject", ws, user)

    e = audit_capture.one(SyncEventType.PROJECT_CREATED)
    assert e.project_id == project.id
    assert e.workspace_id == test_workspace_id
    assert e.metadata["project_name"] == "mergin/myproject"


def test_project_created_from_template(client, audit_capture):
    # Re-assign test_project's creator to the reserved TEMPLATES user so it
    # becomes a template project (this is how the app identifies templates).
    template_user = add_user("TEMPLATES", "pass123")
    template = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    template.creator = template_user
    db.session.commit()

    client.post(
        f"/v1/project/{template.workspace.name}",
        json={"name": "from_template", "template": test_project},
    )

    # filter to the new project only (template re-assignment fires project.updated)
    new_project = Project.query.filter_by(name="from_template").first()
    events = [
        e
        for e in audit_capture.of_type(SyncEventType.PROJECT_CREATED)
        if e.project_id == new_project.id
    ]
    assert len(events) == 1
    assert events[0].metadata.get("created_from_template") == test_project


def test_project_created_from_clone(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    ws = project.workspace

    client.post(
        f"/v1/project/clone/{ws.name}/{test_project}",
        json={"namespace": ws.name, "project": "cloned_project"},
    )

    e = audit_capture.one(SyncEventType.PROJECT_CREATED)
    assert e.metadata.get("cloned_from_id") == str(project.id)
    assert e.metadata.get("cloned_from_name") == f"{ws.name}/{test_project}"


def test_project_updated(audit_capture):
    user = add_user("projupdater", "pass123")
    ws = create_workspace()
    project = create_project("updateme", ws, user)
    db.session.refresh(project)

    project.public = True
    db.session.commit()

    e = audit_capture.one(SyncEventType.PROJECT_UPDATED)
    assert e.metadata["new_public"] is True
    assert e.metadata["old_public"] is False


def test_project_marked_for_deletion(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()

    client.post(f"/v2/projects/{project.id}/scheduleDelete")

    e = audit_capture.one(SyncEventType.PROJECT_MARKED_FOR_DELETION)
    assert e.project_id == project.id
    assert e.workspace_id == project.workspace_id


def test_project_restored(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    client.post(f"/v2/projects/{project.id}/scheduleDelete")
    audit_capture.events.clear()

    client.post(f"/app/project/removed-project/restore/{project.id}")

    assert audit_capture.one(SyncEventType.PROJECT_RESTORED).project_id == project.id


def test_project_deleted(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()

    client.delete(f"/v2/projects/{project.id}")

    assert audit_capture.one(SyncEventType.PROJECT_DELETED).project_id == project.id


def test_project_member_added(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    user = add_user("newmember", "pass123")

    client.post(
        f"/v2/projects/{project.id}/collaborators",
        json={"user": user.email, "role": ProjectRole.READER.value},
    )

    e = audit_capture.one(SyncEventType.PROJECT_MEMBER_ADDED)
    assert e.project_id == project.id
    assert e.metadata["target_email"] == user.email
    assert e.metadata["role"] == ProjectRole.READER.value


def test_project_member_updated(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    user = add_user("updatemember", "pass123")
    project.set_role(user.id, ProjectRole.READER)
    db.session.commit()

    client.patch(
        f"/v2/projects/{project.id}/collaborators/{user.id}",
        json={"role": ProjectRole.EDITOR.value},
    )

    e = audit_capture.one(SyncEventType.PROJECT_MEMBER_UPDATED)
    assert e.metadata["old_role"] == ProjectRole.READER.value
    assert e.metadata["new_role"] == ProjectRole.EDITOR.value


def test_project_member_deleted(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    user = add_user("removemember", "pass123")
    project.set_role(user.id, ProjectRole.READER)
    db.session.commit()

    client.delete(f"/v2/projects/{project.id}/collaborators/{user.id}")

    assert (
        audit_capture.one(SyncEventType.PROJECT_MEMBER_DELETED).metadata["target_email"]
        == user.email
    )


def test_project_access_request_created(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    user = add_user("requester", "pass123")
    login(client, "requester", "pass123")

    client.post(f"/app/project/access-request/{project.workspace.name}/{project.name}")

    e = audit_capture.one(SyncEventType.PROJECT_ACCESS_REQUEST_CREATED)
    assert e.project_id == project.id
    assert e.actor_id == user.id


def test_project_access_request_accepted(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    requester = add_user("acceptrequester", "pass123")
    access_request = AccessRequest(project, requester.id)
    db.session.add(access_request)
    db.session.commit()

    client.post(
        f"/app/project/access-request/accept/{access_request.id}",
        json={"permissions": "read"},
    )

    assert (
        audit_capture.one(SyncEventType.PROJECT_ACCESS_REQUEST_ACCEPTED).metadata[
            "target_email"
        ]
        == requester.email
    )
    # accepting also fires project.member.added
    assert (
        audit_capture.one(SyncEventType.PROJECT_MEMBER_ADDED).metadata["target_email"]
        == requester.email
    )


def test_project_access_request_rejected(client, audit_capture):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    requester = add_user("rejectrequester", "pass123")
    access_request = AccessRequest(project, requester.id)
    db.session.add(access_request)
    db.session.commit()

    client.delete(f"/app/project/access-request/{access_request.id}")

    assert (
        audit_capture.one(SyncEventType.PROJECT_ACCESS_REQUEST_REJECTED).metadata[
            "target_email"
        ]
        == requester.email
    )


def test_project_version_created(client, audit_capture):
    from .utils import file_info
    from . import test_project_dir

    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    # A remove-only push needs no chunk uploads so it's self-contained.
    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "updated": [],
            "removed": [file_info(test_project_dir, "test3.txt")],
        },
    }
    resp = client.post(f"/v2/projects/{project.id}/versions", json=data)
    assert resp.status_code == 201

    e = audit_capture.one(SyncEventType.PROJECT_VERSION_CREATED)
    assert e.project_id == project.id
    assert e.metadata["version"] == "v2"


def test_project_version_created_v1_no_upload(client, audit_capture):
    """V1 push with only removals takes the no-upload fast path in project_push."""
    from .utils import file_info
    from . import test_project_dir

    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "updated": [],
            "removed": [file_info(test_project_dir, "test3.txt")],
        },
    }
    resp = client.post(
        f"/v1/project/push/{project.workspace.name}/{project.name}", json=data
    )
    assert resp.status_code == 200

    e = audit_capture.one(SyncEventType.PROJECT_VERSION_CREATED)
    assert e.project_id == project.id
    assert e.metadata["version"] == "v2"


def test_project_version_created_v1_push_finish(client, audit_capture):
    """V1 push with file uploads goes through push_finish."""
    import os
    from .utils import file_info
    from . import test_project_dir

    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    filename = "test.qgs"
    filepath = os.path.join(test_project_dir, filename)
    # "updated" because the fixture already uploaded all test_project_dir files at v1.
    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "updated": [file_info(test_project_dir, filename)],
            "removed": [],
        },
    }
    resp = client.post(
        f"/v1/project/push/{project.workspace.name}/{project.name}", json=data
    )
    assert resp.status_code == 200
    upload_id = resp.json["transaction"]
    for chunk_id in data["changes"]["updated"][0]["chunks"]:
        with open(filepath, "rb") as f:
            client.post(
                f"/v1/project/push/chunk/{upload_id}/{chunk_id}",
                data=f.read(1024),
                headers={"Content-Type": "application/octet-stream"},
            )
    resp = client.post(f"/v1/project/push/finish/{upload_id}")
    assert resp.status_code == 200

    e = audit_capture.one(SyncEventType.PROJECT_VERSION_CREATED)
    assert e.project_id == project.id
    assert e.metadata["version"] == "v2"


def test_project_version_created_from_template(client, audit_capture):
    """Creating a project from a template emits PROJECT_VERSION_CREATED for the v1."""
    template_user = add_user("TEMPLATES", "pass123")
    template = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    template.creator = template_user
    db.session.commit()
    audit_capture.events.clear()

    client.post(
        f"/v1/project/{template.workspace.name}",
        json={"name": "from_template_audit", "template": test_project},
    )

    new_project = Project.query.filter_by(name="from_template_audit").first()
    events = [
        e
        for e in audit_capture.of_type(SyncEventType.PROJECT_VERSION_CREATED)
        if e.project_id == new_project.id
    ]
    assert len(events) == 1
    assert events[0].metadata["version"] == "v1"


def test_project_version_created_from_clone(client, audit_capture):
    """Cloning a non-empty project emits PROJECT_VERSION_CREATED for the v1."""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    ws = project.workspace

    client.post(
        f"/v1/project/clone/{ws.name}/{test_project}",
        json={"namespace": ws.name, "project": "cloned_audit"},
    )

    cloned = Project.query.filter_by(name="cloned_audit").first()
    events = [
        e
        for e in audit_capture.of_type(SyncEventType.PROJECT_VERSION_CREATED)
        if e.project_id == cloned.id
    ]
    assert len(events) == 1
    assert events[0].metadata["version"] == "v1"
