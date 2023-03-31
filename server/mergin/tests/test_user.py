# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
from unittest.mock import patch

from ..auth.models import User, UserProfile
from ..sync.models import Project
from .. import db
from ..celery import send_email_async
from . import test_project, test_workspace_name, test_workspace_id, json_headers


@patch("mergin.celery.send_email_async.apply_async")
def test_mail_notifications(send_email_mock, client):
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    # need for private project
    project.access.public = False
    db.session.add(project)
    # add some tester
    test_user = User(
        username="tester", passwd="tester", is_admin=False, email="tester@mergin.com"
    )
    test_user.verified_email = True
    test_user.profile = UserProfile()
    db.session.add(test_user)
    test_user2 = User(
        username="tester2", passwd="tester2", is_admin=False, email="tester2@mergin.com"
    )
    test_user2.active = True
    test_user2.verified_email = True
    test_user2.profile = UserProfile()
    db.session.add(test_user2)
    db.session.commit()

    # add tests user as reader to project
    data = {"access": {"readers": project.access.readers + [test_user.id]}}
    resp = client.put(
        "/v1/project/{}/{}".format(test_workspace_name, test_project),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert test_user.id in project.access.readers
    call_args, _ = send_email_mock.call_args
    _, email_data = call_args
    assert test_user.email in email_data["recipients"]

    # disable notifications for test_user, and promote test_user and test_user2 to writers
    user_profile = UserProfile.query.filter_by(user_id=test_user.id).first()
    user_profile.receive_notifications = False
    data = {"access": {"writers": project.access.readers + [test_user2.id]}}
    resp = client.put(
        "/v1/project/{}/{}".format(test_workspace_name, test_project),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert test_user.id in project.access.writers
    assert test_user2.id in project.access.writers
    call_args, _ = send_email_mock.call_args
    _, email_data = call_args
    # only test_user2 receives notification
    assert test_user.email not in email_data["recipients"]
    assert test_user2.email in email_data["recipients"]
