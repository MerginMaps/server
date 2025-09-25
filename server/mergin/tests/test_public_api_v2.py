# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
import shutil
from unittest.mock import patch
import uuid
from pygeodiff import GeoDiffLibError

from .utils import add_user, diffs_are_equal, execute_query, push_change
from ..app import db
from tests import test_project, test_workspace_id
from ..config import Configuration
from ..sync.models import FileDiff, FileHistory, Project, ProjectFilePath, ProjectRole


def test_schedule_delete_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 204
    updated = Project.query.get(project.id)
    assert updated.removed_at and updated.removed_by
    assert updated.storage_params
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 404


def test_delete_project_now(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    original_creator_id = project.creator_id
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 204
    db.session.rollback()
    assert project.creator_id == original_creator_id
    project = Project.query.get(project.id)
    assert project.removed_at and not project.storage_params and not project.files
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 404


def test_delete_after_schedule(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 204
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 204


def test_rename_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    data = {"name": "new_project_name"}
    response = client.patch(f"v2/projects/{project.id}", json=data)
    assert response.status_code == 204
    assert project.name == "new_project_name"
    # name already exists
    response = client.patch(f"v2/projects/{project.id}", json=data)
    assert response.status_code == 409
    # invalid project name
    response = client.patch(f"v2/projects/{project.id}", json={"name": ".new_name"})
    assert response.status_code == 400
    assert response.json["code"] == "InvalidProjectName"
    response = client.patch(
        f"v2/projects/{project.id}", json={"name": ".new_project_name"}
    )
    assert response.status_code == 400
    assert response.json["code"] == "InvalidProjectName"


def test_project_members(client):
    """Test CRUD endpoints for direct project members"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    url = f"v2/projects/{project.id}/collaborators"
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json) == 1

    user = add_user("user", "password")
    # user not a member yet
    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 404

    role = ProjectRole.READER.value
    response = client.patch(url + f"/{user.id}", json={"role": role})
    assert response.status_code == 404

    # add direct access
    response = client.post(url, json={"role": role, "user": user.email})
    assert response.status_code == 201
    assert response.json["id"] == user.id
    assert response.json["project_role"] == role

    Configuration.GLOBAL_READ = 0
    Configuration.GLOBAL_WRITE = 0
    Configuration.GLOBAL_ADMIN = 0
    response = client.get(url)
    assert len(response.json) == 2
    member = next(u for u in response.json if u["id"] == user.id)
    assert member["project_role"] == role
    assert member["workspace_role"] == "guest"

    response = client.patch(
        url + f"/{user.id}", json={"role": ProjectRole.WRITER.value}
    )
    assert response.status_code == 200
    assert response.json["project_role"] == ProjectRole.WRITER.value

    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 204

    response = client.get(url)
    assert len(response.json) == 1

    # test access only by workspace role
    Configuration.GLOBAL_READ = 1
    response = client.get(url)
    member = next(u for u in response.json if u["id"] == user.id)
    assert not member["project_role"]
    assert member["workspace_role"] == "reader"

    # access provided by workspace role cannot be removed directly
    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 404


def test_file_diff_download(client, diff_project):
    """Test download of gpkg diff files"""
    gpkg_file = ProjectFilePath.query.filter_by(
        project_id=diff_project.id, path="base.gpkg"
    ).first()

    diff_file = FileDiff.query.filter_by(
        file_path_id=gpkg_file.id, version=4, rank=0
    ).first()

    response = client.get(f"v2/projects/{diff_project.id}/raw/diff/{diff_file.path}")
    assert response.status_code == 200
    assert response.content_type == "application/octet-stream"

    # add some indented merged diff to db, v5-v8
    basefile = FileHistory.get_basefile(gpkg_file.id, 8)
    diff = FileDiff(
        basefile=basefile,
        version=8,
        rank=1,
        path=f"base.gpkg-{uuid.uuid4()}",
        size=None,
        checksum=None,
    )
    db.session.add(diff)
    db.session.commit()
    assert not os.path.exists(diff.abs_path)

    # download merged diff with its reconstuction on the fly
    response = client.get(f"v2/projects/{diff_project.id}/raw/diff/{diff.path}")
    assert response.status_code == 200
    assert response.content_type == "application/octet-stream"
    assert os.path.exists(diff.abs_path)

    response = client.get(f"v2/projects/{diff_project.id}/raw/diff/{diff.path}+1")
    assert response.status_code == 404


def test_create_diff_checkpoint(diff_project):
    """Test creation of diff checkpoints"""
    # add changes v11-v32 where v9 is a basefile
    file_path_id = (
        ProjectFilePath.query.filter_by(project_id=diff_project.id, path="test.gpkg")
        .first()
        .id
    )

    base_gpkg = os.path.join(diff_project.storage.project_dir, "test.gpkg")
    shutil.copy(
        os.path.join(diff_project.storage.project_dir, "v9", "test.gpkg"), base_gpkg
    )
    for i in range(22):
        sql = f"UPDATE simple SET rating={i}"
        execute_query(base_gpkg, sql)
        pv = push_change(
            diff_project, "updated", "test.gpkg", diff_project.storage.project_dir
        )
        assert diff_project.latest_version == pv.name == (11 + i)
        file_diff = FileDiff.query.filter_by(
            file_path_id=file_path_id, version=pv.name, rank=0
        ).first()
        assert file_diff and os.path.exists(file_diff.abs_path)

    basefile, diffs = FileHistory.diffs_chain(file_path_id, 32)
    assert basefile.project_version_name == 9
    # so far we only have individual diffs
    assert len(diffs) == 22

    # diff for v17-v20 from individual diffs
    diff = FileDiff(
        basefile=basefile, path=f"test.gpkg-diff-{uuid.uuid4()}", version=20, rank=1
    )
    db.session.add(diff)
    db.session.commit()
    assert not os.path.exists(diff.abs_path)
    diff.construct_checkpoint()
    assert os.path.exists(diff.abs_path)

    basefile, diffs = FileHistory.diffs_chain(file_path_id, 20)
    assert basefile.project_version_name == 9
    # 6 individual diffs (v11-v16) + merged diff (v17-v20) as the last one
    assert len(diffs) == 7
    assert diffs[-1] == diff

    # repeat - nothing to do
    mtime = os.path.getmtime(diff.abs_path)
    diff.construct_checkpoint()
    assert mtime == os.path.getmtime(diff.abs_path)

    # diff for v17-v32 with merged diffs (using one above)
    diff = FileDiff(
        basefile=basefile, path=f"test.gpkg-diff-{uuid.uuid4()}", version=32, rank=2
    )
    db.session.add(diff)
    db.session.commit()
    diff.construct_checkpoint()
    assert os.path.exists(diff.abs_path)

    # assert gpkg diff is the same as it would be from merging all individual diffs
    individual_diffs = (
        FileDiff.query.filter_by(file_path_id=file_path_id, rank=0)
        .filter(FileDiff.version.between(17, 32))
        .all()
    )
    merged_diff = os.path.join(diff_project.storage.diffs_dir, "merged-diff")
    diff_project.storage.geodiff.concat_changes(
        [d.abs_path for d in individual_diffs], merged_diff
    )
    assert diffs_are_equal(diff.abs_path, merged_diff)

    # test various failures
    with patch.object(diff_project.storage.geodiff, "concat_changes") as mock:
        # diff for missing basefile (e.g. deleted file or not-existing file)
        diff = FileDiff(
            basefile=basefile, path=f"test.gpkg-diff-{uuid.uuid4()}", version=8, rank=1
        )
        db.session.add(diff)
        db.session.commit()
        diff.construct_checkpoint()
        assert not mock.called

        # geodiff failure
        mock.side_effect = GeoDiffLibError
        diff = FileDiff(
            basefile=basefile, path=f"test.gpkg-diff-{uuid.uuid4()}", version=16, rank=1
        )
        db.session.add(diff)
        db.session.commit()
        diff.construct_checkpoint()
        assert mock.called
        assert not os.path.exists(diff.abs_path)
