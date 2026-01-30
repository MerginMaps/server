# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import current_app
from flask_mail import Mail
from unittest.mock import patch

from ..app import db
from ..config import Configuration
from ..sync.models import (
    Project,
    AccessRequest,
    ProjectRole,
    ProjectVersion,
)
from ..celery import send_email_async
from ..sync.config import Configuration as SyncConfiguration
from ..sync.tasks import (
    remove_temp_files,
    remove_projects_backups,
    create_project_version_zip,
    remove_projects_archives,
    remove_unused_chunks,
)
from ..sync.storages.disk import move_to_tmp
from . import test_project, test_workspace_name, test_workspace_id
from ..sync.utils import get_chunk_location
from . import (
    test_project,
    test_workspace_name,
    test_workspace_id,
    test_project_dir,
    json_headers,
)
from .utils import (
    CHUNK_SIZE,
    add_user,
    create_workspace,
    create_project,
    login,
    modify_file_times,
)
from ..auth.models import User


def test_send_email(app):
    """Test celery is actually sending emails."""
    mail = Mail()
    email_data = {
        "subject": "test",
        "html": "test",
        "recipients": ["foo@bar.com"],
        "sender": "no_reply@cloudmergin.com",
    }
    with mail.record_messages() as outbox:
        Configuration.MERGIN_TESTING = True
        task = send_email_async.s(**email_data).apply()
        assert len(outbox) == 1
        assert task.status == "SUCCESS"
        assert outbox[0].sender == "no_reply@cloudmergin.com"
        assert outbox[0].html == "test"
        assert outbox[0].subject == "test"
        assert current_app.config["MAIL_BCC"] not in outbox[0].bcc
        assert "foo@bar.com" in outbox[0].send_to

        # turn off testing mode
        Configuration.MERGIN_TESTING = False
        task = send_email_async.s(**email_data).apply()
        assert len(outbox) == 2
        assert task.status == "SUCCESS"
        assert current_app.config["MAIL_BCC"] in outbox[1].bcc

    Configuration.MERGIN_TESTING = True
    del email_data["recipients"]
    task = send_email_async.s(**email_data).apply()
    assert task.status == "FAILURE"
    assert "No recipients have been added" in task.traceback


@patch("mergin.celery.send_email_async.apply_async")
def test_send_email_from_flask(send_email_mock, client):
    """Test correct data are passed to celery task which is called from endpoint."""
    user = User.query.filter(User.username == "mergin").first()
    test_workspace = create_workspace()
    p = create_project("testx", test_workspace, user)
    p.set_role(user.id, ProjectRole.OWNER)
    user2 = add_user("test_user", "ilovemergin")
    login(client, "test_user", "ilovemergin")
    email_data = {
        "subject": "Project access requested",
        "recipients": [user.email],
        "sender": current_app.config["MAIL_DEFAULT_SENDER"],
    }
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{p.name}",
        headers=json_headers,
    )
    access_request = AccessRequest.query.filter(
        AccessRequest.project_id == p.id
    ).first()
    assert resp.status_code == 200
    assert access_request.requested_by == user2.id

    assert send_email_mock.called
    call_args, _ = send_email_mock.call_args
    _, kwargs = call_args
    del kwargs["html"]
    assert email_data == kwargs


def test_clean_temp_files(app):
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    # pretend project has been removed
    path = move_to_tmp(project.storage.project_dir)
    assert os.path.exists(path)
    # try with default value, dir is still not marked for removal
    remove_temp_files()
    assert os.path.exists(path)
    # patch modification time of parent dir
    t = datetime.utcnow() - timedelta(days=(app.config["TEMP_EXPIRATION"] + 1))
    parent_dir = os.path.dirname(path)
    os.utime(parent_dir, (datetime.timestamp(t), datetime.timestamp(t)))
    remove_temp_files()
    assert not os.path.exists(path)


def test_remove_deleted_project_backups(client):
    resp = client.delete("/v1/project/{}/{}".format(test_workspace_name, test_project))
    assert resp.status_code == 200
    rp = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    # move removal to past, so it is picked by celery job
    rp.removed_at = datetime.utcnow() - timedelta(
        days=(client.application.config["DELETED_PROJECT_EXPIRATION"] + 1)
    )
    rp_dir = rp.storage.project_dir
    assert os.path.exists(rp_dir)
    db.session.commit()
    remove_projects_backups()
    assert not Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).count()
    assert not os.path.exists(rp_dir)
    # project still exists in db
    rm_project = Project.query.get(rp.id)
    assert (
        rm_project.removed_at
        and not rm_project.storage_params
        and not rm_project.files
        and rm_project.project_users == []
    )
    assert (
        not Project.query.filter_by(id=rm_project.id)
        .filter(Project.storage_params.isnot(None))
        .first()
    )
    assert ProjectVersion.query.filter_by(project_id=rm_project.id).count() != 0
    assert str(rm_project.id) in rm_project.name


def test_create_project_version_zip(diff_project):
    """Test celery tasks for creating project zip and cleaning them up"""
    latest_version = diff_project.get_latest_version()
    zip_path = Path(latest_version.zip_path)
    partial_zip_path = Path(latest_version.zip_path + ".partial")
    assert not zip_path.exists()
    create_project_version_zip(diff_project.latest_version)
    assert zip_path.exists()
    assert not partial_zip_path.exists()
    before_mtime = zip_path.stat().st_mtime
    # mock expired partial zip -> celery removes it and creates new zip
    partial_zip_path.parent.mkdir(parents=True, exist_ok=True)
    partial_zip_path.touch()
    new_time = datetime.now(timezone.utc) - timedelta(
        seconds=current_app.config["PARTIAL_ZIP_EXPIRATION"] + 1
    )
    modify_file_times(partial_zip_path, new_time)
    create_project_version_zip(diff_project.latest_version)
    assert (
        not partial_zip_path.exists()
    )  # after creating zip archive, celery remove partial zip
    after_mtime = zip_path.stat().st_mtime
    assert before_mtime < after_mtime
    # mock valid partial zip -> celery skips creating new zip and returns
    before_mtime = zip_path.stat().st_mtime
    partial_zip_path.parent.mkdir(parents=True, exist_ok=True)
    partial_zip_path.touch()
    create_project_version_zip(diff_project.latest_version)
    assert (
        partial_zip_path.exists()
    )  # celery does not create zip archive and does not clean partial zip
    after_mtime = zip_path.stat().st_mtime
    assert before_mtime == after_mtime
    os.remove(partial_zip_path)
    remove_projects_archives()  # zip is valid -> keep
    assert zip_path.exists()
    new_time = datetime.now(timezone.utc) - timedelta(
        days=current_app.config["PROJECTS_ARCHIVES_EXPIRATION"] + 1
    )
    modify_file_times(latest_version.zip_path, new_time)
    remove_projects_archives()  # zip has expired -> remove
    assert not os.path.exists(latest_version.zip_path)


def test_remove_chunks(app):
    """Test cleanup of outdated chunks"""
    # pretend chunks were uploaded
    chunks = []
    src_file = os.path.join(test_project_dir, "base.gpkg")
    with open(src_file, "rb") as in_file:
        f_size = os.path.getsize(src_file)
        for i in range(math.ceil(f_size / CHUNK_SIZE)):
            chunk_id = str(uuid.uuid4())
            chunk_location = get_chunk_location(chunk_id)
            os.makedirs(os.path.dirname(chunk_location), exist_ok=True)
            with open(chunk_location, "wb") as out_file:
                out_file.write(in_file.read(CHUNK_SIZE))
            chunks.append(chunk_location)

    remove_unused_chunks()
    assert all(os.path.exists(chunk) for chunk in chunks)

    def _atime_mock(path: str) -> float:
        """Mock file stats to be already expired"""
        return (
            datetime.now(timezone.utc)
            - timedelta(seconds=SyncConfiguration.UPLOAD_CHUNKS_EXPIRATION)
        ).timestamp() - 1

    with patch("os.path.getatime", _atime_mock):
        remove_unused_chunks()
        assert not any(os.path.exists(chunk) for chunk in chunks)
