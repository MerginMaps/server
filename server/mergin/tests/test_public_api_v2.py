# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
import shutil
from typing import List
from unittest.mock import patch
import uuid
from pygeodiff import GeoDiffLibError

from .utils import (
    add_user,
    create_project,
    create_workspace,
    diffs_are_equal,
    execute_query,
    login_as_admin,
    push_change,
)
from ..app import db
from tests import test_project, test_workspace_id
from ..config import Configuration
from ..sync.models import (
    FileDiff,
    FileHistory,
    Project,
    ProjectFilePath,
    ProjectRole,
    ProjectVersionDelta,
)
from ..sync.files import DeltaChange, PushChangeType
from ..sync.utils import is_versioned_file
from sqlalchemy.exc import IntegrityError
import pytest
from datetime import datetime, timedelta, timezone

from mergin.app import db
from mergin.config import Configuration
from mergin.sync.errors import (
    BigChunkError,
    DiffDownloadError,
    ProjectLocked,
    ProjectVersionExists,
    AnotherUploadRunning,
    StorageLimitHit,
    UploadError,
)
from mergin.sync.files import ChangesSchema
from mergin.sync.models import (
    Project,
    ProjectRole,
    ProjectVersion,
    SyncFailuresHistory,
    Upload,
)
from mergin.sync.utils import get_chunk_location
from . import TMP_DIR, test_project, test_workspace_id, test_project_dir
from .test_project_controller import (
    CHUNK_SIZE,
    _get_changes,
    _get_changes_with_diff,
    _get_changes_with_diff_0_size,
    _get_changes_without_added,
)
from .utils import add_user, file_info


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

    # try with reconstruction failure
    with patch.object(FileDiff, "construct_checkpoint") as construct_checkpoint_mock:
        os.remove(diff.abs_path)
        construct_checkpoint_mock.return_value = False
        response = client.get(f"v2/projects/{diff_project.id}/raw/diff/{diff.path}")
        assert response.status_code == 422
        assert response.json["code"] == DiffDownloadError.code

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


def test_delta_merge_changes():
    """Test merging of delta changes works as expected"""

    create = DeltaChange(
        path="file1.gpkg",
        change=PushChangeType.CREATE,
        version=1,
        size=100,
        checksum="abc",
    )
    update = DeltaChange(
        path="file1.gpkg",
        change=PushChangeType.UPDATE,
        version=2,
        size=120,
        checksum="def",
    )
    delete = DeltaChange(
        path="file1.gpkg",
        change=PushChangeType.DELETE,
        version=3,
        size=0,
        checksum="ghi",
    )
    update_diff1 = DeltaChange(
        path="file1.gpkg",
        change=PushChangeType.UPDATE_DIFF,
        version=4,
        size=130,
        checksum="xyz",
        diff="diff1",
    )
    update_diff2 = DeltaChange(
        path="file1.gpkg",
        change=PushChangeType.UPDATE_DIFF,
        version=5,
        size=140,
        checksum="uvw",
        diff="diff2",
    )

    # CREATE + UPDATE -> CREATE
    merged = ProjectVersionDelta.merge_changes([create, update])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.CREATE
    assert merged[0].version == create.version
    # check reverse order as well
    merged = ProjectVersionDelta.merge_changes([update, create])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.CREATE
    assert merged[0].version == create.version

    # CREATE + DELETE -> removed
    merged = ProjectVersionDelta.merge_changes([create, delete])
    assert len(merged) == 0

    # UPDATE + DELETE -> DELETE
    merged = ProjectVersionDelta.merge_changes([update, delete])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.DELETE

    # CREATE + UPDATE_DIFF -> CREATE
    merged = ProjectVersionDelta.merge_changes([create, update_diff1])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.CREATE
    assert merged[0].diffs == []

    # UPDATE + UPDATE_DIFF -> UPDATE
    merged = ProjectVersionDelta.merge_changes([update, update_diff1])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.UPDATE
    assert merged[0].diffs == []

    # UPDATE_DIFF + UPDATE_DIFF -> merged diffs
    merged = ProjectVersionDelta.merge_changes([update_diff1, update_diff2])
    assert len(merged) == 1
    assert merged[0].change == PushChangeType.UPDATE_DIFF
    assert merged[0].version == update_diff2.version
    assert merged[0].size == update_diff2.size
    assert merged[0].checksum == update_diff2.checksum
    assert [d.path for d in merged[0].diffs] == ["diff1", "diff2"]


def test_project_version_delta_changes(client, diff_project: Project):
    """Test that get_delta_changes and its schema work as expected"""
    latest_version = diff_project.get_latest_version()
    project_id = diff_project.id
    assert latest_version.name == 10
    assert diff_project.get_delta_changes(2, 1) is None
    assert diff_project.get_delta_changes(2, 2) is None
    deltas: List[ProjectVersionDelta] = (
        ProjectVersionDelta.query.filter_by(project_id=project_id)
        .order_by(ProjectVersionDelta.version)
        .all()
    )
    assert len(deltas) == 10
    initial_delta = deltas[0]
    initial_version = ProjectVersion.query.filter_by(
        project_id=project_id, name=initial_delta.version
    ).first()
    assert initial_version
    assert initial_delta.version
    assert initial_delta.rank == 0
    assert initial_delta.version == 1

    delta = diff_project.get_delta_changes(1, 2)
    assert len(delta) == 1
    assert delta[0].change == PushChangeType.DELETE
    # no ranks created as we get here just first version with get_delta
    assert ProjectVersionDelta.query.filter_by(rank=1).count() == 0

    # delete + create version
    delta = diff_project.get_delta_changes(1, 3)
    assert len(delta) == 1
    assert delta[0].change == PushChangeType.CREATE
    assert delta[0].version == 3
    assert delta[0].checksum == deltas[3].changes[0]["checksum"]

    # get_delta with update diff
    delta = diff_project.get_delta_changes(1, 4)
    assert len(delta) == 1
    assert delta[0].change == PushChangeType.CREATE
    assert ProjectVersionDelta.query.filter_by(rank=1).count() == 0

    # create rank 1 checkpoint for v4
    delta = diff_project.get_delta_changes(0, 4)
    checkpoint_changes = ProjectVersionDelta.query.filter_by(rank=1)
    filediff_checkpoints = FileDiff.query.filter_by(rank=1)
    checkpoint_change = checkpoint_changes.first()
    assert checkpoint_changes.count() == 1
    assert checkpoint_change.version == deltas[3].version
    assert filediff_checkpoints.count() == 0
    # check if filediff basefile is correctly set
    file_history = FileHistory.query.filter_by(project_version_name=4).first()
    assert len(delta) == len(initial_version.files)
    delta_base_gpkg = next((d for d in delta if d.path == "base.gpkg"), None)
    assert delta_base_gpkg
    # from history is clear, that we are just creating geopackage in this range
    assert delta_base_gpkg.change == PushChangeType.CREATE
    assert delta_base_gpkg.version == 3
    assert delta_base_gpkg.path == file_history.path
    assert delta_base_gpkg.size == file_history.size
    assert delta_base_gpkg.checksum == file_history.checksum
    assert len(delta_base_gpkg.diffs) == 0

    # get data with multiple ranks = 1 level checkpoints 1-4, 5-8 + checkpoint 9 and 10
    delta = diff_project.get_delta_changes(0, 10)
    assert len(delta) == len(latest_version.files)
    delta_test_gpkg = next((d for d in delta if d.path == "test.gpkg"), None)
    assert delta_test_gpkg
    assert delta_test_gpkg.change == PushChangeType.CREATE
    assert ProjectVersionDelta.query.filter_by(rank=1).count() == 2
    # base gpgk is transparent
    assert not next((c for c in delta if c.path == "base.gpkg"), None)

    delta = diff_project.get_delta_changes(latest_version.name - 3, latest_version.name)
    delta_base_gpkg = next((c for c in delta if c.path == "base.gpkg"), None)
    assert delta_base_gpkg.change == PushChangeType.DELETE

    # create just update_diff versions with checkpoint
    base_gpkg = os.path.join(diff_project.storage.project_dir, "test.gpkg")
    shutil.copy(
        os.path.join(diff_project.storage.project_dir, "v9", "test.gpkg"), base_gpkg
    )
    for i in range(6):
        sql = f"UPDATE simple SET rating={i}"
        execute_query(base_gpkg, sql)
        push_change(
            diff_project, "updated", "test.gpkg", diff_project.storage.project_dir
        )
    delta = diff_project.get_delta_changes(8, latest_version.name + 6)
    assert len(delta) == 2
    # file history in 9.th version is basefile
    fh = FileHistory.query.filter_by(
        project_version_name=latest_version.name - 1
    ).first()
    base_gpkg_checkpoint = FileDiff.query.filter_by(basefile_id=fh.id, rank=1).first()
    assert base_gpkg_checkpoint
    assert base_gpkg_checkpoint.version == latest_version.name + 6

    fh = FileHistory.query.filter_by(
        project_version_name=latest_version.name + 6
    ).first()
    delta = diff_project.get_delta_changes(12, latest_version.name + 6)
    assert len(delta) == 1
    assert len(delta[0].diffs) == 1
    assert delta[0].diffs[0].path == base_gpkg_checkpoint.path
    assert delta[0].change == PushChangeType.UPDATE_DIFF
    assert delta[0].checksum == fh.checksum
    assert delta[0].size == fh.size

    # check if checkpoint will be there
    response = client.get(
        f"v2/projects/{diff_project.id}/raw/diff/{delta[0].diffs[0].path}"
    )
    assert response.status_code == 200


push_data = [
    # success
    (
        {"version": "v1", "changes": _get_changes_without_added(test_project_dir)},
        201,
        None,
    ),
    # with diff, success
    ({"version": "v1", "changes": _get_changes_with_diff(test_project_dir)}, 201, None),
    # just a dry-run
    (
        {
            "version": "v1",
            "changes": _get_changes_with_diff(test_project_dir),
            "check_only": True,
        },
        204,
        None,
    ),
    # only delete files
    (
        {
            "version": "v1",
            "changes": {
                "added": [],
                "removed": [
                    file_info(test_project_dir, "base.gpkg"),
                ],
                "updated": [],
            },
        },
        201,
        None,
    ),
    # broken .gpkg file
    (
        {"version": "v1", "changes": _get_changes_with_diff_0_size(test_project_dir)},
        422,
        UploadError.code,
    ),
    # contains already uploaded file
    (
        {"version": "v1", "changes": _get_changes(test_project_dir)},
        422,
        UploadError.code,
    ),
    # version mismatch
    (
        {"version": "v0", "changes": _get_changes_without_added(test_project_dir)},
        409,
        ProjectVersionExists.code,
    ),
    # no changes requested
    (
        {"version": "v1", "changes": {"added": [], "removed": [], "updated": []}},
        422,
        UploadError.code,
    ),
    # inconsistent changes, a file cannot be added and updated at the same time
    (
        {
            "version": "v1",
            "changes": {
                "added": [
                    {
                        "path": "test.txt",
                        "size": 1234,
                        "checksum": "9adb76bf81a34880209040ffe5ee262a090b62ab",
                        "chunks": [],
                    }
                ],
                "removed": [],
                "updated": [
                    {
                        "path": "test.txt",
                        "size": 1234,
                        "checksum": "9adb76bf81a34880209040ffe5ee262a090b62ab",
                        "chunks": [],
                    }
                ],
            },
        },
        422,
        UploadError.code,
    ),
    # inconsistent changes, a file which does not exist cannot be deleted
    (
        {
            "version": "v1",
            "changes": {
                "added": [],
                "removed": [
                    {
                        "path": "not-existing.txt",
                        "size": 1234,
                        "checksum": "9adb76bf81a34880209040ffe5ee262a090b62ab",
                    }
                ],
                "updated": [],
            },
        },
        422,
        UploadError.code,
    ),
    # missing version (required parameter)
    ({"changes": _get_changes_without_added(test_project_dir)}, 400, None),
    # incorrect changes format
    ({"version": "v1", "changes": {}}, 400, None),
]


@pytest.mark.parametrize("data,expected,err_code", push_data)
def test_create_version(client, data, expected, err_code):
    """Test project push endpoint with different payloads."""

    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    assert project.latest_version == 1

    chunks = []
    if expected == 201:
        # mimic chunks were uploaded
        for f in data["changes"]["added"] + data["changes"]["updated"]:
            src_file = (
                os.path.join(TMP_DIR, f["diff"]["path"])
                if f.get("diff")
                else os.path.join(test_project_dir, f["path"])
            )
            with open(src_file, "rb") as in_file:
                for chunk in f["chunks"]:
                    chunk_location = get_chunk_location(chunk)
                    os.makedirs(os.path.dirname(chunk_location), exist_ok=True)
                    with open(chunk_location, "wb") as out_file:
                        out_file.write(in_file.read(CHUNK_SIZE))

                    chunks.append(chunk_location)

    response = client.post(f"v2/projects/{project.id}/versions", json=data)
    assert response.status_code == expected
    if expected == 201:
        assert response.json["version"] == "v2"
        assert project.latest_version == 2
        assert all(not os.path.exists(chunk) for chunk in chunks)
    else:
        assert project.latest_version == 1
        if err_code:
            assert response.json["code"] == err_code
            failure = SyncFailuresHistory.query.filter_by(project_id=project.id).first()
            # failures are not created when POST request body is invalid (caught by connexion validators)
            if failure:
                assert failure.last_version == "v1"
                assert failure.error_type == "project_push"


def test_create_version_failures(client):
    """Test various project push failures beyond invalid payload"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()

    data = {"version": "v1", "changes": _get_changes_without_added(test_project_dir)}

    # somebody else is syncing
    upload = Upload(project, 1, _get_changes(test_project_dir), 1)
    db.session.add(upload)
    db.session.commit()
    os.makedirs(upload.upload_dir)
    open(upload.lockfile, "w").close()

    response = client.post(f"v2/projects/{project.id}/versions", json=data)
    assert response.status_code == 409
    assert response.json["code"] == AnotherUploadRunning.code
    upload.clear()

    # project is locked
    project.locked_until = datetime.now(timezone.utc) + timedelta(days=1)
    db.session.commit()
    response = client.post(f"v2/projects/{project.id}/versions", json=data)
    assert response.status_code == 423
    assert response.json["code"] == ProjectLocked.code
    project.locked_until = None
    db.session.commit()

    # try to finish the transaction which would fail on storage limit
    with patch.object(
        Configuration,
        "GLOBAL_STORAGE",
        0,
    ):
        response = client.post(f"v2/projects/{project.id}/versions", json=data)
        assert response.status_code == 422
        assert response.json["code"] == StorageLimitHit.code

    # try to finish the transaction which would fail on version created integrity error, e.g. race conditions
    with patch.object(
        ProjectVersion,
        "__init__",
        side_effect=IntegrityError("Cannot insert new version", None, None),
    ):
        # keep just deleted data to avoid messing with chunks
        data["changes"]["added"] = data["changes"]["updated"] = []
        response = client.post(f"v2/projects/{project.id}/versions", json=data)
        assert response.status_code == 422
        assert response.json["code"] == UploadError.code

    # try to finish the transaction which would fail on existing Upload integrity error, e.g. race conditions
    with patch.object(
        Upload,
        "__init__",
        side_effect=IntegrityError("Cannot insert upload", None, None),
    ):
        response = client.post(f"v2/projects/{project.id}/versions", json=data)
        assert response.status_code == 409
        assert response.json["code"] == AnotherUploadRunning.code

    # try to finish the transaction which would fail on unexpected integrity error
    # patch of ChangesSchema is just a workaround to trigger and error
    with patch.object(
        ChangesSchema,
        "validate",
        side_effect=IntegrityError("Cannot insert upload", None, None),
    ):
        response = client.post(f"v2/projects/{project.id}/versions", json=data)
        assert response.status_code == 409


def test_upload_chunk(client):
    """Test pushing a chunk to a project"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    url = f"/v2/projects/{project.id}/chunks"
    client.application.config["MAX_CHUNK_SIZE"] = (
        1024  # Set a small max chunk size for testing
    )
    max_chunk_size = client.application.config["MAX_CHUNK_SIZE"]

    response = client.post(
        url,
        data=b"a" * (max_chunk_size + 1),  # Exceeding max chunk size
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413
    assert response.json["code"] == BigChunkError.code

    # Project is locked, cannot push chunks
    project.locked_until = datetime.now(timezone.utc) + timedelta(weeks=26)
    db.session.commit()
    response = client.post(
        url,
        data=b"a",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 423
    assert response.json["code"] == ProjectLocked.code

    project.locked_until = None  # Unlock the project
    project.removed_at = datetime.now(timezone.utc) - timedelta(
        days=(client.application.config["DELETED_PROJECT_EXPIRATION"] + 1)
    )  # Ensure project is removed
    db.session.commit()
    response = client.post(
        url,
        data=b"a",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 404

    # Push a chunk successfully
    project.removed_at = None  # Ensure project is not removed
    db.session.commit()
    response = client.post(
        url,
        data=b"a" * max_chunk_size,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    chunk_id = response.json["id"]
    assert chunk_id
    valid_until = response.json["valid_until"]
    valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%dT%H:%M:%S%z")
    assert valid_until_dt > datetime.now(timezone.utc)
    assert valid_until_dt < datetime.now(timezone.utc) + timedelta(
        seconds=client.application.config["UPLOAD_CHUNKS_EXPIRATION"]
    )
    # Check if the chunk is stored correctly
    stored_chunk = get_chunk_location(chunk_id)
    assert os.path.exists(stored_chunk)
    with open(stored_chunk, "rb") as f:
        assert f.read() == b"a" * max_chunk_size


def test_full_push(client):
    """Test full project push with upload of chunks and project version creation"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()

    # prepare data to push
    project_dir = os.path.join(TMP_DIR, test_project)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    shutil.copytree(test_project_dir, project_dir)
    os.rename(
        os.path.join(project_dir, "base.gpkg"),
        os.path.join(project_dir, "new_base.gpkg"),
    )

    test_file = file_info(project_dir, "new_base.gpkg", chunk_size=CHUNK_SIZE)
    uploaded_chunks = []

    with open(os.path.join(project_dir, test_file["path"]), "rb") as in_file:
        for _ in test_file["chunks"]:
            data = in_file.read(CHUNK_SIZE)
            response = client.post(
                f"/v2/projects/{project.id}/chunks",
                data=data,
                headers={"Content-Type": "application/octet-stream"},
            )
            assert response.status_code == 200
            uploaded_chunks.append(response.json["id"])
            chunk_location = get_chunk_location(response.json["id"])
            assert os.path.exists(chunk_location)

    test_file["chunks"] = uploaded_chunks

    response = client.post(
        f"v2/projects/{project.id}/versions",
        json={
            "version": "v1",
            "changes": {"added": [test_file], "updated": [], "removed": []},
        },
    )
    assert response.status_code == 201
    assert response.json["version"] == "v2"
    assert project.latest_version == 2
    assert os.path.exists(
        os.path.join(project.storage.project_dir, "v2", test_file["path"])
    )
    assert not Upload.query.filter_by(project_id=project.id).first()


def test_project_delta(client, diff_project):
    """Test project delta endpoint"""
    login_as_admin(client)
    user = add_user()
    workspace = create_workspace()
    initial_project = create_project("empty_project", workspace=workspace, user=user)
    working_dir = os.path.join(TMP_DIR, "empty_work_dir")
    os.makedirs(os.path.join(TMP_DIR, "empty_work_dir"), exist_ok=True)
    # add basefile
    shutil.copy(
        os.path.join(test_project_dir, "base.gpkg"),
        os.path.join(working_dir, "base.gpkg"),
    )
    push_change(initial_project, "added", "base.gpkg", working_dir)
    response = client.get(f"v2/projects/{initial_project.id}/delta?since=0")
    assert response.status_code == 200
    delta = response.json
    assert len(delta) == 1
    assert delta[0]["change"] == PushChangeType.CREATE.value
    assert delta[0]["version"] == 1

    # remove the file and get changes from 0 -> 2 where base gpgkg is removed -> transparent
    push_change(initial_project, "removed", "base.gpkg", working_dir)
    response = client.get(f"v2/projects/{initial_project.id}/delta?since=0")
    assert response.status_code == 200
    delta = response.json
    assert len(delta) == 0

    # non valid cases
    response = client.get(f"v2/projects/{diff_project.id}/delta")
    assert response.status_code == 400
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=2&to=1")
    assert response.status_code == 400
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=-2")
    assert response.status_code == 400
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=-2&to=-1")
    assert response.status_code == 400
    # exceeding latest version
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=0&to=2000")
    assert response.status_code == 400
    # no changes between versions with same number
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=1&to=1")
    assert response.status_code == 400

    # since 1 to latest version
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=1")
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["change"] == PushChangeType.CREATE.value
    assert response.json[0]["version"] == 9
    files = (
        ProjectVersion.query.filter_by(
            project_id=diff_project.id, name=response.json[0]["version"]
        )
        .first()
        .files
    )

    # simple update
    response = client.get(f"v2/projects/{diff_project.id}/delta?since=4&to=8")
    assert response.status_code == 200
    delta = response.json
    assert len(delta) == 1

    # simulate pull of delta[0]
    assert delta[0]["change"] == PushChangeType.UPDATE.value
    assert delta[0]["version"] == 5
    assert not delta[0].get("diffs")


# integration test for pull mechanism
def test_project_pull_diffs(client, diff_project):
    """Test project pull mechanisom in v2 with diff files"""
    since = 5
    to = 7
    # check diff files in database where we can get them with right order and metadata
    current_diffs = (
        FileDiff.query.filter(FileDiff.version > since, FileDiff.version <= to)
        .order_by(FileDiff.version)
        .all()
    )
    response = client.get(f"v2/projects/{diff_project.id}/delta?since={since}&to={to}")
    assert response.status_code == 200
    delta = response.json
    assert len(delta) == 1
    assert delta[0]["change"] == PushChangeType.UPDATE_DIFF.value
    assert delta[0]["version"] == 7
    first_diff = delta[0]["diffs"][0]
    second_diff = delta[0]["diffs"][1]
    assert first_diff["path"] == current_diffs[0].path
    assert second_diff["path"] == current_diffs[1].path
    response = client.get(
        f"v2/projects/{diff_project.id}/raw/diff/{first_diff['path']}"
    )
    assert response.status_code == 200
