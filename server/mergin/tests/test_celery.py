# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Mail
from unittest.mock import patch

from .. import db
from ..config import Configuration
from ..sync.models import Project
from ..celery import send_email_async
from ..sync.tasks import remove_temp_files, remove_projects_backups
from ..sync.storages.disk import move_to_tmp
from . import test_project, test_workspace_name, test_workspace_id
from .utils import cleanup, add_user


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
    usr = add_user("test1", "test")
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name="test"
    ).first()
    readers = project.access.readers.copy()
    readers.append(usr.id)
    project.access.readers = readers
    db.session.commit()
    email_data = {
        "subject": "Mergin project mergin/test has been deleted",
        "recipients": [usr.email],
        "sender": current_app.config["MAIL_DEFAULT_SENDER"],
    }
    resp = client.delete("/v1/project/{}/{}".format("mergin", "test"))
    assert resp.status_code == 200
    # cleanup files
    cleanup(client, [project.storage.project_dir])
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
    parent_dir = os.path.dirname(os.path.dirname(path))
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
