# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import shutil

import pytest
import os
from pathlib import Path

from mergin.auth.models import User
from mergin.sync.models import Project, ProjectVersion
from mergin.tests import (
    test_project,
    test_workspace_id,
    test_workspace_name,
    DEFAULT_USER,
)
from mergin.sync.config import Configuration as sync_config

test_create_project_data = [
    # missing arguments
    # (("my_project",), 2, "Missing argument"),
    # # existing project
    # (
    #     (
    #         test_project,
    #         test_workspace_name,
    #         DEFAULT_USER[0],
    #     ),
    #     1,
    #     "ERROR: Project name already exists",
    # ),
    # # not existing creator user
    # (
    #     (
    #         "my_project",
    #         test_workspace_name,
    #         "not_existing",
    #     ),
    #     1,
    #     "ERROR: User not found",
    # ),
    # # not existing workspace
    # (
    #     (
    #         "my_project",
    #         "not_existing",
    #         DEFAULT_USER[0],
    #     ),
    #     1,
    #     "ERROR: Workspace not found",
    # ),
    # success
    (
        (
            "my_project",
            test_workspace_name,
            DEFAULT_USER[0],
        ),
        0,
        "Project created",
    ),
]


@pytest.mark.parametrize("args,code,output", test_create_project_data)
def test_create_project(runner, args, code, output):
    """Test create project command"""
    # create project
    create = runner.invoke(args=["project", "create", *args])
    assert create.exit_code == code
    assert output in create.output

    if code == 0:
        project = Project.query.filter_by(
            name="my_project", workspace_id=test_workspace_id
        ).first()
        assert ProjectVersion.query.filter_by(project_id=project.id).count()


test_create_user_data = [
    (
        (
            f" {DEFAULT_USER[0].upper()}  ",
            "Il0veMergin",
            "--email",
            f"{DEFAULT_USER[0]}@example.com",
        ),
        "ERROR: User already exists",
        1,
    ),  # existing username after lowercasing and stripping whitespaces
    (
        ("cli_user", "Il0veMergin"),
        "Error: Missing option '--email'",
        2,
    ),  # missing email argument
    (
        (
            " cli_user ",
            "Il0veMergin",
            "--is-admin",
            "--email",
            "  CLI_USER@example.com ",
        ),
        "User created",
        0,
    ),  # success
]


@pytest.mark.parametrize("args,output,code", test_create_user_data)
def test_create_user(runner, args, output, code):
    """Test create user command"""
    result = runner.invoke(args=["user", "create", *args])
    assert result.exit_code == code
    assert output in result.output
    if code == 0:
        user = User.query.filter_by(username="cli_user").first()
        assert user.is_admin
        assert user.email == "cli_user@example.com"


download_project_data = [
    (
        (
            f" {test_workspace_name}/{test_project}  ",
            "--version",
            1,
            "--directory",
            sync_config.TEMP_DIR,
        ),
        0,
        "Project downloaded",
    ),
    (
        (
            f"{test_workspace_name}/non-existing",
            "--version",
            1,
            "--directory",
            sync_config.TEMP_DIR,
        ),
        1,
        "ERROR: Project does not exist",
    ),
    (
        (
            f"{test_workspace_name}/{test_project}",
            "--version",
            2,
            "--directory",
            sync_config.TEMP_DIR,
        ),
        1,
        "ERROR: Project version does not exist",
    ),
    (
        (
            f"{test_workspace_name}/{test_project}",
            "--version",
            1,
            "--directory",
            "/tmp",
        ),
        1,
        "ERROR: Destination directory '/tmp' already exist",
    ),
]


@pytest.mark.parametrize("args,code,output", download_project_data)
def test_download_project(runner, args, code, output):
    """Test download project command"""
    if os.path.exists(sync_config.TEMP_DIR):
        shutil.rmtree(sync_config.TEMP_DIR)
    result = runner.invoke(args=["project", "download", *args])
    assert result.exit_code == code
    assert output in result.output
    if code == 0:
        assert os.path.exists(sync_config.TEMP_DIR) and os.path.isdir(
            sync_config.TEMP_DIR
        )


remove_project_data = [
    (
        f" {test_workspace_name}/{test_project}  ",
        0,
        "Project removed",
    ),
    (
        f" {test_workspace_name}/non-existing  ",
        1,
        "ERROR: Project does not exist",
    ),
]


@pytest.mark.parametrize("project_name,code,output", remove_project_data)
def test_remove_project(runner, project_name, code, output):
    """Test remove project command"""
    remove = runner.invoke(args=["project", "remove", project_name])
    assert remove.exit_code == code
    assert output in remove.output
    if code == 0:
        project = Project.query.filter_by(
            name=test_project, workspace_id=test_workspace_id
        ).first()
        assert project.removed_at
        assert not project.removed_by
