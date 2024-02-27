# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import datetime

from .. import db
from ..config import Configuration
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
    assert ws.get_user_role(user) == "guest"
    assert not ws.user_has_permissions(user, "owner")
    assert not ws.user_has_permissions(user, "read")
    assert not ws.user_has_permissions(user, "write")
    assert not ws.user_has_permissions(user, "admin")
    assert ws.disk_usage() == 0  # no projects so far
    # user is kind of guest, without any global permissions
    assert len(handler.list_active()) == 1
    assert handler.list_active()[0].name == ws.name
    assert len(handler.list_user_workspaces(user.username)) == 1
    assert handler.list_user_workspaces(user.username)[0].name == ws.name
    # change global flag to enable user push to any project
    Configuration.GLOBAL_WRITE = True
    assert ws.user_has_permissions(user, "write")
    assert ws.user_has_permissions(user, "read")
    assert not ws.user_has_permissions(user, "admin")
    assert not ws.user_has_permissions(user, "owner")

    Configuration.GLOBAL_ADMIN = True
    # create project with dummy file to count for workspace usage
    project = create_project("test_permissions", ws, user)
    project.files = [
        {
            "path": "some_file.txt",
            "location": "v1/some_file.txt",
            "size": 1024,
            "checksum": "89469a6482267de394c7c7270cb7ffafe694ea76",
        }
    ]
    project.disk_usage = 1024
    db.session.commit()
    assert ws.disk_usage() == 1024
    # mark project for removal
    project.removed_at = datetime.datetime.utcnow()
    project.removed_by = user.id
    db.session.commit()
    assert ws.disk_usage() == 0


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
