# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from mergin.sync.tasks import remove_transaction_chunks
from . import DEFAULT_USER
from .utils import (
    add_user,
    logout,
    login_as_admin,
    create_workspace,
    create_project,
    upload_file_to_project,
    login,
    file_info,
)

from ..auth.models import User
import os
import shutil
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError
import pytest
from datetime import datetime, timedelta, timezone
import json

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
from ..sync.interfaces import WorkspaceRole


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
    Configuration.GLOBAL_READ = 0


def test_get_project(client):
    """Test get project info endpoint"""
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    test_workspace = create_workspace()
    project = create_project("new_project", test_workspace, admin)
    logout(client)
    # anonymous user cannot access the private resource
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 404
    # lack of permissions
    user = add_user("tests", "tests")
    login(client, user.username, "tests")
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 403
    # access public project
    project.public = True
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 200
    assert response.json["public"] is True
    # project scheduled for deletion
    login_as_admin(client)
    project.public = False
    project.removed_at = datetime.utcnow()
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 404
    # success
    project.removed_at = None
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 200
    expected_keys = {
        "id",
        "name",
        "workspace",
        "role",
        "version",
        "created_at",
        "updated_at",
        "public",
        "size",
    }
    assert expected_keys == response.json.keys()
    # create new versions
    files = ["test.txt", "test3.txt", "test.qgs"]
    for file in files:
        upload_file_to_project(project, file, client)
    # project version does not exist
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version+1}"
    )
    assert response.status_code == 200
    assert response.json["id"] == str(project.id)
    assert "files" not in response.json.keys()
    # files
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version-2}"
    )
    assert response.status_code == 200
    assert len(response.json["files"]) == 1
    assert any(resp_files["path"] == files[0] for resp_files in response.json["files"])
    assert not any(
        resp_files["path"] == files[1] for resp_files in response.json["files"]
    )
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version}"
    )
    assert len(response.json["files"]) == 3
    assert {f["path"] for f in response.json["files"]} == set(files)
    # invalid version format parameter
    response = client.get(f"v2/projects/{project.id}?files_at_version=3")
    assert response.status_code == 400


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
    chunk_ids = []
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
                    chunk_ids.append(chunk)

    with patch(
        "mergin.sync.public_api_v2_controller.remove_transaction_chunks.delay"
    ) as mock_remove:
        response = client.post(f"v2/projects/{project.id}/versions", json=data)
    assert response.status_code == expected
    if expected == 201:
        assert response.json["version"] == "v2"
        assert project.latest_version == 2
        # chunks exists after upload, cleanup job did not remove them
        assert all(os.path.exists(chunk) for chunk in chunks)
        if chunk_ids:
            assert mock_remove.called_once_with(chunk_ids)
        remove_transaction_chunks(chunk_ids)
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


def test_create_version_object_deleted_error(client):
    """Test that ObjectDeletedError during push returns 422 without secondary exception"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()

    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "removed": [
                file_info(test_project_dir, "base.gpkg"),
            ],
            "updated": [],
        },
    }

    # Create a real ObjectDeletedError by using internal SQLAlchemy state
    def raise_object_deleted(*args, **kwargs):
        # Create a minimal state-like object that ObjectDeletedError can use
        class FakeState:
            class_ = Upload

            def obj(self):
                return None

        raise ObjectDeletedError(FakeState())

    with patch.object(
        ProjectVersion,
        "__init__",
        side_effect=raise_object_deleted,
    ):
        response = client.post(f"v2/projects/{project.id}/versions", json=data)

    # Should return 422 UploadError, not 500 from secondary exception
    assert response.status_code == 422
    assert response.json["code"] == UploadError.code


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


def test_list_workspace_projects(client):
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    test_workspace = create_workspace()
    url = f"v2/workspaces/{test_workspace.id}/projects"
    for i in range(1, 11):
        create_project(f"project_{i}", test_workspace, admin)

    # missing required query params
    assert client.get(url).status_code == 400

    # success
    page = 1
    per_page = 10
    response = client.get(url + f"?page={page}&per_page={per_page}")
    resp_data = json.loads(response.data)
    assert response.status_code == 200
    assert resp_data["count"] == 11
    assert len(resp_data["projects"]) == per_page
    # correct number on the last page
    page = 4
    per_page = 3
    response = client.get(url + f"?page={page}&per_page={per_page}")
    assert response.json["count"] == 11
    assert len(response.json["projects"]) == 2
    # name search - more results
    page = 1
    per_page = 3
    response = client.get(
        url + f"?page={page}&per_page={per_page}&q=1&order_params=updated ASC"
    )
    assert response.json["count"] == 2
    assert len(response.json["projects"]) == 2
    assert response.json["projects"][1]["name"] == "project_10"
    # name search - specific result
    project_name = "project_4"
    response = client.get(url + f"?page={page}&per_page={per_page}&q={project_name}")
    assert response.json["projects"][0]["name"] == project_name
    # sorting
    response = client.get(
        url + f"?page={page}&per_page={per_page}&q=1&order_params=created DESC"
    )
    assert response.json["projects"][0]["name"] == "project_10"

    # no permissions to workspace
    user2 = add_user("user", "password")
    login(client, user2.username, "password")
    with patch.object(
        Configuration,
        "GLOBAL_READ",
        0,
    ), patch.object(
        Configuration,
        "GLOBAL_WRITE",
        0,
    ), patch.object(
        Configuration,
        "GLOBAL_ADMIN",
        0,
    ):
        resp = client.get(url + "?page=1&per_page=10")
        assert resp.status_code == 200
        assert resp.json["count"] == 0

    # no existing workspace
    assert (
        client.get("/v1/workspace/1234/projects?page=1&per_page=10").status_code == 404
    )

    # project shared directly
    p = Project.query.filter_by(workspace_id=test_workspace.id).first()
    p.set_role(user2.id, ProjectRole.READER)
    db.session.commit()
    resp = client.get(url + "?page=1&per_page=10")
    resp_data = json.loads(resp.data)
    assert resp_data["count"] == 1
    assert resp_data["projects"][0]["name"] == p.name

    # deactivate project
    p.removed_at = datetime.utcnow()
    db.session.commit()
    resp = client.get(url + "?page=1&per_page=10")
    assert resp.json["count"] == 0

    # add user as a reader
    with patch.object(Configuration, "GLOBAL_READ", 1):
        resp = client.get(url + "?page=1&per_page=10")
        assert p.name not in [proj["name"] for proj in resp.json["projects"]]
        assert resp.json["count"] == 10

    # logout
    logout(client)
    assert client.get(url + "?page=1&per_page=10").status_code == 401
