# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import shutil

import pytest
import os
from unittest.mock import patch

# from flask import current_app

from mergin.auth.models import User
from mergin.sync.models import Project, ProjectVersion
from mergin.tests import (
    test_project,
    test_workspace_id,
    test_workspace_name,
    DEFAULT_USER,
    test_project_dir,
)
from mergin.sync.config import Configuration as sync_config


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
        1,
        "ERROR: Project name already exists",
    ),
    # not existing creator user
    (
        (
            "my_project",
            test_workspace_name,
            "not_existing",
        ),
        1,
        "ERROR: User not found",
    ),
    # not existing workspace
    (
        (
            "my_project",
            "not_existing",
            DEFAULT_USER[0],
        ),
        1,
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
    # success
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
    # project does not exist in the workspace
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
    # request project version does not exist
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
    # destination dir already exists
    (
        (
            f"{test_workspace_name}/{test_project}",
            "--version",
            1,
            "--directory",
            test_project_dir,
        ),
        1,
        f"ERROR: Destination directory '{test_project_dir}' already exists",
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


@pytest.mark.parametrize("collect_stats", [True, False])
@patch("mergin.stats.tasks.send_statistics.delay")
@patch("mergin.stats.tasks.save_statistics.delay")
@patch("mergin.commands._check_celery")
@patch("mergin.commands._echo_title")
def test_send_statistics(
    mock_echo_title,
    mock_check_celery,
    mock_save_statistics,
    mock_send_statistics,
    collect_stats,
    app,
):
    """Test send statistics helper"""
    from mergin.commands import _send_statistics

    mock_echo_title.return_value = ""
    mock_check_celery.return_value = True
    mock_save_statistics.return_value = None
    mock_send_statistics.return_value = None
    app.config["COLLECT_STATISTICS"] = 1 if collect_stats else 0

    _send_statistics(app)
    assert mock_save_statistics.call_count == 1
    assert mock_send_statistics.call_count == (1 if collect_stats else 0)


test_check_email_data = [
    (0, 1, 1, 1, "Email sent."),  # success
    (0, 1, 1, 0, ""),  # celery is not running
    (
        1,
        1,
        1,
        1,
        "Sending emails is disabled. Please set MAIL_SUPPRESS_SEND=False to enable sending emails.",
    ),  # emails are suppressed
    (0, 0, 1, 1, "Error: Missing option '--email'"),  # email parameter is missing
    (0, 1, 0, 1, "No default sender set."),  # default sender is missing
]


@patch("mergin.celery.send_email_async.delay")
@patch("mergin.commands._check_celery")
@pytest.mark.parametrize(
    "suppressed,recipient,sender,celery_check,output", test_check_email_data
)
def test_check_email(
    mock_check_celery,
    mock_send_email,
    suppressed,
    recipient,
    sender,
    celery_check,
    output,
    runner,
    app,
):
    """Test check_email command"""
    mock_send_email.return_value = None
    mock_check_celery.return_value = celery_check
    app.config["MAIL_SUPPRESS_SEND"] = suppressed
    app.config["MAIL_DEFAULT_SENDER"] = "sender@mergin.com" if sender else None

    result = runner.invoke(
        args=[
            "server",
            "send-check-email",
            "--email",
            f" test@mergin.com " if recipient else None,
        ]
    )
    assert output in result.output
    sent = 1 if output == "Email sent." else 0
    assert mock_send_email.call_count == sent
