# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import datetime
import os

from sqlalchemy import null

from ..app import db
from ..config import Configuration
from ..sync.interfaces import WorkspaceRole
from ..sync.models import FileHistory, ProjectVersion, PushChangeType, ProjectFilePath
from ..sync.workspace import GlobalWorkspaceHandler
from .utils import add_user, login, create_project


def test_workspace_implementation(client):
    """Test global implementation of workspace"""
    handler = GlobalWorkspaceHandler()
    user = add_user("user", "password")

    assert not handler.get_by_name("foo")
    ws = handler.get_by_name(Configuration.GLOBAL_WORKSPACE)
    assert ws.storage == Configuration.GLOBAL_STORAGE
    assert ws.is_active
    Configuration.GLOBAL_READ = False
    Configuration.GLOBAL_WRITE = False
    Configuration.GLOBAL_ADMIN = False
    assert ws.get_user_role(user) == WorkspaceRole.GUEST
    assert not ws.user_has_permissions(user, "owner")
    assert not ws.user_has_permissions(user, "read")
    assert not ws.user_has_permissions(user, "write")
    assert not ws.user_has_permissions(user, "admin")
    # user is kind of guest, without any global permissions
    assert len(handler.list_active()) == 1
    assert handler.list_active()[0].name == ws.name
    assert len(handler.list_user_workspaces(user.username)) == 1
    assert handler.list_user_workspaces(user.username)[0].name == ws.name
    Configuration.GLOBAL_READ = True
    assert ws.user_has_permissions(user, "read")
    assert not ws.user_has_permissions(user, "write")
    # admin is counted as editor
    assert handler.server_editors_count() == 1
    # change global flag to enable user push to any project
    Configuration.GLOBAL_WRITE = True
    assert ws.user_has_permissions(user, "write")
    assert ws.user_has_permissions(user, "read")
    assert handler.server_editors_count() == 2
    assert not ws.user_has_permissions(user, "admin")
    assert not ws.user_has_permissions(user, "owner")

    Configuration.GLOBAL_ADMIN = True
    # create project with dummy file to count for workspace usage
    project = create_project("test_permissions", ws, user)
    latest_version = project.get_latest_version()
    file = ProjectFilePath(project.id, path="some_file.txt")
    file_history = FileHistory(
        file,
        location=os.path.join(
            ProjectVersion.to_v_name(project.latest_version), "some_file.txt"
        ),
        checksum="89469a6482267de394c7c7270cb7ffafe694ea76",
        size=1024,
        diff=None,
        change=PushChangeType.CREATE,
        version_name=latest_version.name,
    )
    file_history.version = latest_version
    default_project_usage = ws.disk_usage()
    db.session.add(file_history)
    project.disk_usage = 1024
    db.session.commit()
    assert ws.disk_usage() == 1024 + default_project_usage
    # mark project for removal
    project.removed_at = datetime.datetime.utcnow()
    project.removed_by = user.id
    db.session.commit()
    assert ws.disk_usage() == default_project_usage
    assert handler.server_editors_count() == 2

    current_time = datetime.datetime.now(datetime.timezone.utc)
    latest_version.created = datetime.datetime.combine(
        current_time.replace(day=1), datetime.time.max
    ) - datetime.timedelta(days=1)
    db.session.commit()
    assert handler.monthly_contributors_count() == 1

    # test group by author_id
    create_project("test_second_project", ws, user)
    latest_version.created = current_time
    db.session.commit()
    assert handler.monthly_contributors_count() == 2


def test_workspace(client):
    """Test get global workspace"""
    resp = client.get("/v1/workspaces")
    assert len(resp.json) == 1
    assert resp.json[0]["name"] == Configuration.GLOBAL_WORKSPACE
    # default logged in user is a super user
    assert resp.json[0]["role"] == "owner"

    resp = client.get("/v1/workspace/1")
    assert resp.json["name"] == Configuration.GLOBAL_WORKSPACE
    assert resp.json["role"] == "owner"

    assert client.get("/v1/workspace/2").status_code == 404

    # login as another user
    Configuration.GLOBAL_READ = False
    Configuration.GLOBAL_WRITE = False
    Configuration.GLOBAL_ADMIN = False
    user = add_user("user", "password")
    login(client, "user", "password")
    resp = client.get("/v1/workspace/1")
    assert resp.json["name"] == Configuration.GLOBAL_WORKSPACE
    assert resp.json["role"] == "guest"
