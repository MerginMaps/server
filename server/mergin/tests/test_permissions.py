# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import pytest
import datetime
from flask_login import AnonymousUserMixin

from mergin.tests import DEFAULT_USER

from ..sync.permissions import (
    require_project,
    require_project_by_many_uuids,
    ProjectPermissions,
)
from ..sync.models import Project, ProjectRole
from ..auth.models import User
from ..app import db
from ..config import Configuration
from .utils import (
    add_user, 
    create_project, 
    create_workspace, 
    login, 
    logout,
)


def test_project_permissions(client):
    owner = add_user("owner", "pwd")
    test_workspace = create_workspace()
    project = create_project("test_permissions", test_workspace, owner)
    project.set_role(owner.id, ProjectRole.OWNER)

    # testing owner permissions -> has all of them
    assert ProjectPermissions.Read.check(project, owner)
    assert ProjectPermissions.Upload.check(project, owner)
    assert ProjectPermissions.Delete.check(project, owner)
    assert ProjectPermissions.Update.check(project, owner)
    assert ProjectPermissions.Edit.check(project, owner)
    assert ProjectPermissions.All.check(project, owner)

    # tests superuser -> has all of them
    user = User.query.filter_by(username="mergin", is_admin=True).first()
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)
    assert ProjectPermissions.Edit.check(project, owner)
    assert ProjectPermissions.All.check(project, user)

    # tests another user in shared workspace -> by default no permissions
    user = add_user()
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    assert not ProjectPermissions.get_user_project_role(project, user)

    # tests user with editor access -> has read access

    project.set_role(user.id, ProjectRole.EDITOR)
    db.session.commit()
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert ProjectPermissions.get_user_project_role(project, user) == ProjectRole.EDITOR

    # adjust global permissions
    Configuration.GLOBAL_READ = True
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    Configuration.GLOBAL_WRITE = True
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    Configuration.GLOBAL_ADMIN = True
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.All.check(project, user)

    # deactivate user -> no permissions
    user.active = False
    project.unset_role(user.id)
    db.session.commit()
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    assert not ProjectPermissions.get_user_project_role(project, user)

    # tests anonymous user -> only has read access if project is public
    user = AnonymousUserMixin()
    assert not ProjectPermissions.Read.check(project, user)
    project.public = True
    db.session.commit()
    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.get_user_project_role(project, user) == ProjectRole.READER

    # tests inactive project (marked for removal)
    project.removed_at = datetime.datetime.utcnow()
    db.session.commit()
    user = User.query.filter_by(username="owner").first()
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Edit.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    assert not ProjectPermissions.get_user_project_role(project, user)

    # only super admin can still access it
    user = User.query.filter_by(username="mergin", is_admin=True).first()
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)
    assert ProjectPermissions.All.check(project, user)
    assert ProjectPermissions.Edit.check(project, user)
    assert ProjectPermissions.get_user_project_role(project, user) == ProjectRole.OWNER

def test_permissions_require_project_by_many_uuids(client):
    """Test require_project_by_many_uuids with various permission scenarios."""
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    test_workspace = create_workspace()

    private_proj = create_project("batch_private", test_workspace, admin)
    public_proj = create_project("batch_public", test_workspace, admin)

    p = Project.query.get(public_proj.id)
    p.public = True
    db.session.commit()

    priv_id = str(private_proj.id)
    pub_id = str(public_proj.id)

    # First user with access to both projects
    login(client, DEFAULT_USER[0], DEFAULT_USER[1])

    with client:
        client.get("/")
        items = require_project_by_many_uuids([priv_id, pub_id], ProjectPermissions.Read)
    assert len(items) == 2
    assert all(not isinstance(i, dict) for i in items)

    # Second user with no access to private project
    user2 = add_user("user_batch", "password")
    login(client, user2.username, "password")

    with client:
        client.get("/")
        items = require_project_by_many_uuids([pub_id, priv_id], ProjectPermissions.Read)
    assert len(items) == 2

    # public -> Project object (no dict error)
    assert not isinstance(items[0], dict)
    assert str(items[0].id) == pub_id

    # private -> dict error 403
    assert isinstance(items[1], dict)
    assert items[1]["id"] == priv_id
    assert items[1]["error"] == 403

    # Logged-out (anonymous) user
    logout(client)

    with client:
        client.get("/")
        items = require_project_by_many_uuids([priv_id, pub_id], ProjectPermissions.Read)

    assert len(items) == 2

    # private project -> hidden
    assert isinstance(items[0], dict)
    assert items[0]["id"] == priv_id
    assert items[0]["error"] == 404

    # public project -> accessible
    assert not isinstance(items[1], dict)
    assert str(items[1].id) == pub_id

    # InvalidUUID
    with pytest.raises(Exception):
        require_project_by_many_uuids(["not-a-uuid"], ProjectPermissions.Read)
