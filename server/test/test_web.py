# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import json
from flask import url_for
from unittest.mock import patch

from src.models.db_models import AccessRequest, Project
from src import db
from src.auth.models import User
from .utils import login, create_project, add_user
from . import json_headers


@patch('src.celery.send_email_async.apply_async')
def test_email_notifications(send_email_mock, client):
    url = url_for('send_email_notification')
    users = User.query.all()
    for user in users:
        user.verified_email = True
        db.session.add(user)
    db.session.commit()
    data = {
        'users': [u.username for u in users],
        'subject': 'Test',
        'message': '<p><h1>Greeting,</h1> this is a <b>test message</b></p>'
    }
    resp = client.post(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    call_args, _ = send_email_mock.call_args
    _, email_data = call_args
    assert data['subject'] == email_data['subject']
    assert data['message'] == email_data['html']
    assert [u.email for u in users] == email_data['bcc']


def test_project_access_request(client):
    user = User.query.filter(User.username == 'mergin').first()
    p = create_project("testx", "mergin", user)

    user2 = add_user("test_user", "ilovemergin")
    login(client, 'test_user', 'ilovemergin')

    url = url_for('create_project_access_request', namespace="mergin", project_name="testx")

    user2.active = False
    db.session.commit()

    # inactive user
    resp = client.post(url, headers=json_headers)
    assert resp.status_code == 409

    user2.active = True
    db.session.commit()

    resp = client.post(url, headers=json_headers)
    access_request = AccessRequest.query.filter(AccessRequest.namespace == "mergin", AccessRequest.project_id == p.id).first()
    assert resp.status_code == 200
    assert access_request.user.username == "test_user"

    # already exists
    resp = client.post(url, headers=json_headers)
    assert resp.status_code == 409

    url2 = url_for('get_project_access_requests')
    resp = client.get(url2, headers=json_headers)
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert resp_data[0]['user']["username"] == "test_user"

    url2 = url_for('delete_project_access_request', request_id=access_request.id)
    resp = client.delete(url2, headers=json_headers)
    assert resp.status_code == 200
    access_request = AccessRequest.query.filter(AccessRequest.namespace == "mergin", AccessRequest.project_id == p.id).first()
    assert access_request is None

    resp = client.post(url, headers=json_headers)
    assert resp.status_code == 200
    access_request = AccessRequest.query.filter(AccessRequest.namespace == "mergin",
                                                AccessRequest.project_id == p.id).first()
    assert access_request.user.username == "test_user"


    url = url_for('accept_project_access_request', request_id=access_request.id)
    data = {"permissions": "write"}
    resp = client.post(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 403

    login(client, 'mergin', 'ilovemergin')
    resp = client.post(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    access_request = AccessRequest.query.filter(AccessRequest.namespace == "mergin", AccessRequest.project_id == p.id).first()
    assert access_request is None
    project = Project.query.filter(Project.name == "testx", Project.namespace == "mergin").first()
    assert user2.id in project.access.readers
    assert user2.id in project.access.writers
    assert user2.id not in project.access.owners
