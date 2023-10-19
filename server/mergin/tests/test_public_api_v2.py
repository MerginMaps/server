# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import json

from mergin.sync.models import Project
from tests import test_project, test_workspace_id, json_headers


def test_schedule_delete_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 204
    updated = Project.query.get(project.id)
    assert updated.removed_at and updated.removed_by
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 404


def test_delete_project_now(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 204
    assert not Project.query.get(project.id)
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
    data = {"name": " new_project_name  "}
    response = client.patch(
        f"v2/projects/{project.id}", data=json.dumps(data), headers=json_headers
    )
    assert response.status_code == 200
    assert project.name == "new_project_name"
    # repeat - the new name is already occupied
    response = client.patch(
        f"v2/projects/{project.id}", data=json.dumps(data), headers=json_headers
    )
    assert response.status_code == 409
    assert response.json["code"] == "ProjectNameAlreadyExists"
    assert "Entered project name already exists" in response.json["detail"]
    # illegal project name
    data = {"name": ".new_name"}
    response = client.patch(
        f"v2/projects/{project.id}", data=json.dumps(data), headers=json_headers
    )
    assert response.status_code == 400
    assert response.json["code"] == "InvalidProjectName"
    assert (
        "Entered project name is invalid, don't start project name with . "
        "and use only alphanumeric or these -._!"
    ) in response.json["detail"]
