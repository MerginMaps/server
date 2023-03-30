# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
from flask_login import AnonymousUserMixin

from ..sync.permissions import require_project, ProjectPermissions
from ..auth.models import User
from .. import db
from ..config import Configuration
from .utils import add_user, create_project, create_workspace


def test_project_permissions(client):
    owner = add_user("owner", "pwd")
    test_workspace = create_workspace()
    project = create_project("test_permissions", test_workspace, owner)

    # testing owner permissions -> has all of them
    assert ProjectPermissions.Read.check(project, owner)
    assert ProjectPermissions.Upload.check(project, owner)
    assert ProjectPermissions.Delete.check(project, owner)
    assert ProjectPermissions.Update.check(project, owner)
    assert ProjectPermissions.All.check(project, owner)

    # tests superuser -> has all of them
    user = User.query.filter_by(username="mergin", is_admin=True).first()
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)
    assert ProjectPermissions.All.check(project, user)

    # tests another user in shared workspace -> by default no permissions
    user = add_user("random", "random")
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    # adjust global permissions
    Configuration.GLOBAL_READ = True
    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    Configuration.GLOBAL_WRITE = True
    assert ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.All.check(project, user)
    Configuration.GLOBAL_ADMIN = True
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.All.check(project, user)

    # deactivate user -> no permissions
    user.active = False
    db.session.commit()
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.All.check(project, user)

    # tests anonymous user -> only has read access if project is public
    user = AnonymousUserMixin()
    assert not ProjectPermissions.Read.check(project, user)
    project.access.public = True
    db.session.commit()
    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)

    # tests inactive project (marked for removal)
    project.removed_at = datetime.datetime.utcnow()
    db.session.commit()
    user = User.query.filter_by(username="owner").first()
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.All.check(project, user)

    # only super admin can still access it
    user = User.query.filter_by(username="mergin", is_admin=True).first()
    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)
    assert ProjectPermissions.All.check(project, user)
