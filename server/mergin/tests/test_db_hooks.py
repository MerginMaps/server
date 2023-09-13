# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from pathlib import Path

from sqlalchemy.orm.attributes import flag_modified
from ..sync.models import (
    Project,
    ProjectVersion,
    Upload,
    ProjectAccess,
    SyncFailuresHistory,
)
from ..auth.models import User, UserProfile
from .. import db
from . import DEFAULT_USER
from .utils import add_user, create_project, create_workspace, cleanup
from ..auth.app import inactivate_user


def test_close_user_account(client, diff_project):
    """Test fully set up and active user is successfully removed incl:
    - user profile
    - associated files
    - project access to created and shared projects
    """
    user_project = "user_proj"
    cleanup(client, [os.path.join("user", user_project)])
    # set up
    user = add_user("user", "user")
    user_id = user.id

    # user has access to mergin user diff_project
    diff_project.access.writers.append(user.id)
    flag_modified(diff_project.access, "writers")
    # user contributed to another user project so he is listed in projects history
    change = {"added": [], "removed": [], "updated": []}
    pv = ProjectVersion(
        diff_project, "v11", user.username, change, diff_project.files, "127.0.0.1"
    )
    diff_project.latest_version = pv.name
    pv.project = diff_project
    db.session.add(pv)
    db.session.add(diff_project)
    # user has it's own project
    test_workspace = create_workspace()
    p = create_project(user_project, test_workspace, user)
    db.session.commit()
    assert user.id in diff_project.access.writers
    proj_resp = client.get(
        f"/v1/project/{diff_project.workspace.name}/{diff_project.name}"
    )
    assert user.id in proj_resp.json["access"]["writers"]
    assert user.username in proj_resp.json["access"]["writersnames"]

    # deactivate user first (direct hack in db to mimic inconsistency)
    user.active = False
    db.session.commit()
    assert user.id in diff_project.access.writers  # not yet removed
    proj_resp = client.get(
        f"/v1/project/{diff_project.workspace.name}/{diff_project.name}"
    )
    assert user.id not in proj_resp.json["access"]["writers"]
    assert user.username not in proj_resp.json["access"]["writersnames"]
    # add failed sync
    diff_project.sync_failed(
        "",
        "push_lost",
        "Push artefact removed by subsequent push",
        user.id,
    )
    # now remove user
    inactivate_user(user)
    db.session.delete(user)
    db.session.commit()
    assert not User.query.filter_by(username="user").count()
    assert not UserProfile.query.filter_by(
        user_id=user_id
    ).count()  # handled as backreference
    # project still exists as it belongs to workspace, not to user
    assert (
        Project.query.filter_by(
            name=user_project, workspace_id=test_workspace.id
        ).count()
        == 1
    )
    assert user_id not in diff_project.access.writers
    # user remains referenced in existing project version he created (as read-only ref)
    assert diff_project.get_latest_version().author == "user"
    sync_fail_history = SyncFailuresHistory.query.filter(
        SyncFailuresHistory.project_id == diff_project.id
    ).all()
    assert len(sync_fail_history) == 1
    assert sync_fail_history[0].user_id is None


def test_remove_project(client, diff_project):
    """Test project is successfully removed incl:
    - pending transfer
    - pending upload
    - project access
    - project versions
    - associated files
    """
    # set up
    mergin_user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    project_dir = Path(diff_project.storage.project_dir)
    changes = {"added": [], "removed": [], "updated": []}
    upload = Upload(diff_project, 10, changes, mergin_user.id)
    db.session.add(upload)
    db.session.commit()
    project_id = diff_project.id

    # remove project
    db.session.delete(diff_project)
    db.session.commit()
    assert not Project.query.filter_by(id=project_id).count()
    assert not Upload.query.filter_by(project_id=project_id).count()
    assert not ProjectVersion.query.filter_by(project_id=project_id).count()
    assert not ProjectAccess.query.filter_by(project_id=project_id).count()
    # files need to be deleted manually
    assert project_dir.exists()
    cleanup(client, [project_dir])
