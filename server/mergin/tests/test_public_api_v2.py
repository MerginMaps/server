# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
from datetime import datetime, timedelta, timezone

from mergin.sync.utils import get_chunk_location

from .utils import add_user
from ..app import db
from mergin.sync.models import Project
from ..tests import test_project, test_workspace_id

from ..config import Configuration
from ..sync.models import ProjectRole
from . import test_project_dir


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


def test_upload_chunk(client, app):
    """Test pushing a chunk to a project"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    url = f"/v2/projects/{project.id}/chunks"
    app.config["MAX_CHUNK_SIZE"] = 1024  # Set a small max chunk size for testing
    max_chunk_size = app.config["MAX_CHUNK_SIZE"]

    response = client.post(
        url,
        data=b"a" * (max_chunk_size + 1),  # Exceeding max chunk size
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413

    # Project is locked, cannot push chunks
    project.locked_until = datetime.now(timezone.utc) + timedelta(weeks=26)
    db.session.commit()
    response = client.post(
        url,
        data=b"a",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 422
    assert response.json["code"] == "ProjectLocked"

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
        seconds=app.config["UPLOAD_CHUNKS_EXPIRATION"]
    )
    # Check if the chunk is stored correctly
    stored_chunk = get_chunk_location(chunk_id)
    assert os.path.exists(stored_chunk)
    with open(stored_chunk, "rb") as f:
        assert f.read() == b"a" * max_chunk_size
