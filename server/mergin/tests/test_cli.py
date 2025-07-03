# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import pytest
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
        ).first()
