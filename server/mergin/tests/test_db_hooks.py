# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ..sync.models import (
    Project,
    ProjectVersion,
    Upload,
    SyncFailuresHistory,
    AccessRequest,
    RequestStatus,
    FileHistory,
    ProjectFilePath,
    LatestProjectFiles,
    ProjectRole,
    ProjectUser,
)
from ..sync.files import UploadChanges
from ..sync.public_api_controller import project_version_created
from ..auth.models import User
from ..app import db
from . import DEFAULT_USER
from .utils import add_user, create_project, create_workspace, cleanup


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
    diff_project.set_role(user.id, ProjectRole.WRITER)
    # user contributed to another user project so he is listed in projects history
    changes = UploadChanges(added=[], updated=[], removed=[])
    pv = ProjectVersion(diff_project, 11, user.id, changes, "127.0.0.1")
    diff_project.latest_version = pv.name
    pv.project = diff_project
    db.session.add(pv)
    db.session.add(diff_project)
    # user has its own project
    test_workspace = create_workspace()
    p = create_project(user_project, test_workspace, user)
    db.session.commit()
    assert diff_project.get_role(user.id) is ProjectRole.WRITER
    proj_resp = client.get(
        f"/v1/project/{diff_project.workspace.name}/{diff_project.name}"
    )
    assert user.id in proj_resp.json["access"]["writers"]
    assert user.username in proj_resp.json["access"]["writersnames"]

    # add pending project access request
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    p2 = create_project("access_request", test_workspace, admin)
    access_request = AccessRequest(p2, user.id)
    db.session.add(access_request)

    # deactivate user first (direct hack in db to mimic inconsistency)
    user.active = False
    db.session.commit()
    assert diff_project.get_role(user.id) is ProjectRole.WRITER  # not yet removed
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
    user.inactivate()
    user.anonymize()
    assert not User.query.filter_by(username="user").count()
    assert user.username.startswith("deleted_")
    assert user.email is None
    assert user.passwd is None
    assert user.profile
    assert user.profile.first_name == user.profile.last_name is None
    # project still exists as it belongs to workspace, not to user
    assert (
        Project.query.filter_by(
            name=user_project, workspace_id=test_workspace.id
        ).count()
        == 1
    )
    assert not diff_project.get_role(user_id)
    # user remains referenced in existing project version he created (as read-only ref)
    assert diff_project.get_latest_version().author_id == user_id
    sync_fail_history = SyncFailuresHistory.query.filter(
        SyncFailuresHistory.project_id == diff_project.id
    ).all()
    assert len(sync_fail_history) == 1
    assert sync_fail_history[0].user_id == user.id
    assert access_request.status == RequestStatus.DECLINED.value


def test_remove_project(client, diff_project):
    """Test project is successfully marked as removed incl:
    - pending upload deleted
    - project access reset
    - project versions deleted
    - associated files deleted
    """
    # set up
    mergin_user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    project_dir = Path(diff_project.storage.project_dir)
    changes = UploadChanges(added=[], removed=[], updated=[])
    upload = Upload(diff_project, 10, changes, mergin_user.id)
    db.session.add(upload)
    project_id = diff_project.id
    user = add_user("user", "user")
    access_request = AccessRequest(diff_project, user.id)
    db.session.add(access_request)
    db.session.commit()
    versions_ids = [
        item.id
        for item in db.session.query(ProjectVersion.id)
        .filter(ProjectVersion.project_id == project_id)
        .all()
    ]
    file_history = FileHistory.query.filter(
        FileHistory.version_id.in_(versions_ids)
    ).first()
    file = os.path.join(project_dir, file_history.location)
    assert file_history and os.path.exists(file)
    original_creator_id = diff_project.creator_id

    # remove project
    diff_project.delete()
    assert Project.query.filter_by(id=project_id).count()
    assert not Upload.query.filter_by(project_id=project_id).count()
    assert ProjectVersion.query.filter_by(project_id=project_id).count()
    assert not ProjectUser.query.filter_by(project_id=project_id).count()
    cleanup(client, [project_dir])
    assert access_request.status == RequestStatus.DECLINED.value
    # after removal cached information in project table remains and project versions, but not files details
    assert diff_project.disk_usage
    assert diff_project.latest_version is not None
    assert diff_project.files == []
    assert diff_project.get_latest_version()
    assert (
        FileHistory.query.filter(FileHistory.version_id.in_(versions_ids)).count() == 0
    )
    assert ProjectFilePath.query.filter_by(project_id=project_id).count() == 0
    assert not os.path.exists(file)
    assert (
        Project.query.filter_by(id=project_id).first().creator_id == original_creator_id
    )
    assert (
        LatestProjectFiles.query.filter_by(project_id=project_id)
        .first()
        .file_history_ids
        == []
    )

    # try to remove the deleted project
    assert diff_project.delete() is None


test_caching_call_data = [
    (4, True),  # success
    (8, True),  # success
    (5, False),  # call not divisible by 4
    (4, False),  # fake last change to be a breaking change
]


@pytest.mark.parametrize("version,called", test_caching_call_data)
@patch("mergin.sync.tasks.create_diff_checkpoint.delay")
def test_trigger_diff_caching(checkpoint_mock, diff_project, version, called):
    # make target version the latest version
    ProjectVersion.query.filter_by(project_id=diff_project.id).filter(
        ProjectVersion.name > version
    ).delete()
    db.session.commit()

    pv = ProjectVersion.query.filter_by(
        project_id=diff_project.id, name=version
    ).first()
    # modify the last change to be a breaking change
    if not called and version == 4:
        fh = FileHistory.query.filter_by(version_id=pv.id, change="update_diff").first()
        fh.change = "delete"
        db.session.commit()

    project_version_created.send(pv)
    assert checkpoint_mock.called == called

    if called:
        # we asked for to cache first level, e.g. with versions 1..4
        _, start, end = checkpoint_mock.call_args[0]
        assert start == version - 3
        assert end == version
