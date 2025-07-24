# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import pytest

from mergin.auth.models import User
from mergin.sync.models import Project
from mergin.tests import (
    test_project,
    test_workspace_id,
    test_workspace_name,
    DEFAULT_USER,
)

test_create_project_data = [
    # missing arguments
    (("my_project",), 2, "Missing argument"),
    # existing project
    (
        (
            test_project,
            test_workspace_name,
            DEFAULT_USER[0],
        ),
        0,
        "ERROR: Project name already exists",
    ),
    # not existing creator user
    (
        (
            "my_project",
            test_workspace_name,
            "not_existing",
        ),
        0,
        "ERROR: User not found",
    ),
    # not existing workspace
    (
        (
            "my_project",
            "not_existing",
            DEFAULT_USER[0],
        ),
        0,
        "ERROR: Workspace not found",
    ),
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
    result = runner.invoke(args=["project", "create", *args])
    assert result.exit_code == code
    assert output in result.output

    if output == "Project created":
        assert Project.query.filter_by(
            name="my_project", workspace_id=test_workspace_id
        ).count()


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
