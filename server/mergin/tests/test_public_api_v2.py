# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
import shutil
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
import pytest
from datetime import datetime, timedelta, timezone

from mergin.app import db
from mergin.config import Configuration
from mergin.sync.errors import (
    BigChunkError,
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
        assert response.json["name"] == "v2"
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
    assert response.json["name"] == "v2"
    assert project.latest_version == 2
    assert os.path.exists(
        os.path.join(project.storage.project_dir, "v2", test_file["path"])
    )
    assert not Upload.query.filter_by(project_id=project.id).first()
