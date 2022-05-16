# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import os
import shutil
import pytest
import json
from datetime import timedelta
from flask import current_app, url_for
from src import db
from src.auth.models import User
from src.models.db_models import (
    Project,
    ProjectTransfer,
    Namespace,
    Upload,
    ProjectAccess,
    ProjectVersion,
    AccessRequest)

from . import test_project, test_namespace, json_headers, TMP_DIR, DEFAULT_USER, test_project_dir, TEST_ORG
from .utils import add_user, login, create_project


test_uploaded_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_uploaded_files')
CHUNK_SIZE = 1024

add_project_transfer_data = [
    (DEFAULT_USER, test_namespace, test_project, {'namespace': 'user'}, 201),  # success
    (DEFAULT_USER, test_namespace, test_project, {'namespace': 'user'}, 409),  # try to transfer project already on transfer
    (DEFAULT_USER, test_namespace, test_project, {'namespace': test_namespace}, 400),  # origin and destination namespaces are the same
    (DEFAULT_USER, test_namespace, test_project, {'namespace': 'user2'}, 404),  # destination namespace does not exist
    (DEFAULT_USER, test_namespace, 'test_error', {'namespace': 'user'}, 404),  # source project does not exist
    (DEFAULT_USER, test_namespace, test_project, {'user': 'user'}, 400),  # missing data['namespace']
    (('user', 'user'), test_namespace, test_project, {'namespace': 'user'}, 403),  # try with unprivileged user
]


@pytest.mark.parametrize("user, namespace, project_name, data, expected", add_project_transfer_data)
def test_create_transfer_project(client, user, namespace, project_name, data, expected):
    """ Test create project transfer from mergin namespace to different namespace """
    add_user('user', 'user')
    login(client, user[0], user[1])
    url = '/v1/project/transfer/{}/{}'.format(namespace, project_name)
    resp = client.post(url, data=json.dumps(data), headers=json_headers)
    if expected == 409:
        resp = client.post(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if resp.status_code == 201:
        u = User.query.filter_by(username=user[0]).first()
        project = Project.query.filter_by(name=project_name, namespace=namespace).first()
        transfer = ProjectTransfer.query.first()
        assert transfer.project_id == project.id
        assert transfer.from_ns_name == namespace
        assert transfer.to_ns_name == data['namespace']
        assert transfer.requested_by == u.id


@pytest.fixture(scope='function')
def project_transfer_init(diff_project):
    """ Creates testing fixture of ProjectTransfer of mergin/test with history (diff_project) to user namespace """
    user = add_user('user', 'user')
    add_user('user2', 'user2')  # dummy user to permission checks
    namespace = Namespace.query.filter_by(name='user').first()
    mergin_user = User.query.filter_by(username='mergin').first()
    project_transfer = ProjectTransfer(diff_project, namespace, mergin_user.id)
    db.session.add(project_transfer)
    return project_transfer


test_get_transfer_project_data = [
    (('user', 'user'), 'user', 'incoming', 1, 200),  # user has 1 transfer request (target)
    (DEFAULT_USER, 'mergin', 'outcoming', 1, 200),  # mergin has 1 transfer request (creator)
    (('user2', 'user2'), 'user2', 'incoming', 0, 200),  # user2 doesn't have any transfer request
    (('user2', 'user2'), 'user', 'incoming', 0, 403),  # user2 can not check others users transfers
]


@pytest.mark.parametrize("user, namespace, direction, count, expected", test_get_transfer_project_data)
def test_get_transfer_project(client, project_transfer_init, user, namespace, direction, count, expected):
    """ Test list of existing project transfer """
    login(client, user[0], user[1])
    resp = client.get(f'/v1/project/transfer/{namespace}', headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        assert len(resp.json) == count
        if count:
            key = 'to_ns_name' if direction == 'incoming' else 'from_ns_name'
            assert resp.json[0][key] == namespace


test_delete_transfer_project_data = [
    (None, DEFAULT_USER, 200),  # success for creator
    (None, ('user', 'user'), 200),  # accepting user can also remove a transfer
    (None, ('user2', 'user2'), 403),  # unrelated user can not remove transfer
    (1, DEFAULT_USER, 404)  # the id of transfer project does not exist
]


@pytest.mark.parametrize("id, user, expected", test_delete_transfer_project_data)
def test_delete_transfer_project(client, project_transfer_init, id, user, expected):
    """ Testing delete project transfer for mergin for different namespace """
    login(client, user[0], user[1])
    id = id if id else project_transfer_init.id
    resp = client.delete(f'/v1/project/transfer/{id}', headers=json_headers)
    assert resp.status_code == expected
    if resp.status_code == 200:
        assert not ProjectTransfer.query.count()


test_execute_transfer_project_data = [
    (None, ('user2', 'user2'), 'Test', True, 403),  # unprivileged user
    (None, DEFAULT_USER, 'Test', True,  403),  # creator of transfer can not accept it
    (1, ('user', 'user'), 'Test', True, 404),  # transfer project does not exist
    (None, ('user', 'user'), 'Test', True, 200),  # transfer project with using original name
    (None, ('user', 'user'), 'Test', False, 200),  # transfer project with using original name and no permissions transferred
    (None, ('user', 'user'), 'My Test', True, 200),  # transfer project with using new name
]


@pytest.mark.parametrize("id, user, project_name, transfer_permission, expected", test_execute_transfer_project_data)
def test_execute_transfer_project_to_user(client, project_transfer_init, id, user, project_name, transfer_permission, expected):
    """ Test acceptance of project transfer """
    # cleanup after previous tests
    transferred_data = os.path.join(current_app.config['LOCAL_PROJECTS'], 'user', project_name)
    if os.path.exists(transferred_data):
        shutil.rmtree(transferred_data)

    id = id if id else project_transfer_init.id
    # keep information before original project gets deleted
    original_project = Project.query.filter_by(namespace=test_namespace, name=test_project).first()
    original_proj_id = original_project.id
    original_owner_id = original_project.creator.id
    original_data_dir = original_project.storage.project_dir

    login(client, user[0], user[1])

    # test if all project access requests are deleted during project transfer
    if expected == 200:
        url = url_for('create_project_access_request', namespace=test_namespace, project_name=test_project)
        resp = client.post(url, headers=json_headers)
        assert resp.status_code == 200
        access_request = AccessRequest.query.filter(AccessRequest.namespace == test_namespace,
                                                    AccessRequest.project_id == original_project.id).first()
        assert access_request

    data = {
        'name': project_name,
        'transfer_permissions': transfer_permission
    }
    resp = client.post(f'/v1/project/transfer/{id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if resp.status_code == 200:
        transferred_project = Project.query.filter_by(namespace=user[0], name=project_name).first()
        assert transferred_project
        assert transferred_project.creator.username == user[0]
        # check original project has been modified (changed namespace) and files on disk were not touched
        assert os.path.exists(original_data_dir)
        assert Project.query.filter_by(id=original_proj_id).first().id == transferred_project.id
        assert not Project.query.filter_by(namespace=test_namespace, name=test_project).first()
        assert not AccessRequest.query.filter(AccessRequest.namespace == test_namespace,
                                              AccessRequest.project_id == original_proj_id).first()

        # check the permission transfer
        for key in ['owners', 'readers', 'writers']:
            attr = getattr(transferred_project.access, key)
            if transfer_permission:
                assert len(attr) == 2 and original_owner_id in attr
            else:
                assert len(attr) == 1 and attr[0] == transferred_project.creator.id


def test_transfer_failures(client, project_transfer_init):
    """ Test failing scenarios for accepting project transfer """
    # cleanup after previous tests
    proj_data = os.path.join(current_app.config['LOCAL_PROJECTS'], 'user', 'foo')
    if os.path.exists(proj_data):
        shutil.rmtree(proj_data)

    login(client, 'user', 'user')
    data = {'name': 'Test', 'transfer_permissions': True}
    user = User.query.filter_by(username='user').first()

    # decrease limit
    ns = Namespace.query.filter_by(name=user.username).first()
    ns.storage = 0
    db.session.add(ns)
    db.session.commit()
    resp = client.post(f'/v1/project/transfer/{project_transfer_init.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'Disk quota reached'

    # create upload for project in transfer
    ns.storage = 100000
    db.session.add(ns)
    upload = Upload(
        project_transfer_init.project,
        10,
        {},
        project_transfer_init.project.creator_id
    )
    db.session.add(upload)
    db.session.commit()
    resp = client.post(f'/v1/project/transfer/{project_transfer_init.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400
    assert 'There is ongoing upload' in resp.json['detail']

    # make transfer expired
    db.session.delete(upload)
    project_transfer_init.expire = project_transfer_init.expire - timedelta(seconds=client.application.config['TRANSFER_EXPIRATION'])
    db.session.add(project_transfer_init)
    db.session.commit()
    resp = client.post(f'/v1/project/transfer/{project_transfer_init.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'The request is already expired'

    project_transfer_init.expire = project_transfer_init.expire + timedelta(seconds=client.application.config['TRANSFER_EXPIRATION'])
    db.session.add(project_transfer_init)
    db.session.commit()

    # create conflict project
    create_project('foo', 'user', user)
    data = {'name': 'foo', 'transfer_permissions': True}
    resp = client.post(f'/v1/project/transfer/{project_transfer_init.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 409
    assert resp.json['detail'] == "Project user/foo already exists"


def test_transfer_to_org(client, test_organisation):
    """ Test project transfer from user namespace to organisation (with him as owner) """
    # clean up
    proj_data = os.path.join(current_app.config['LOCAL_PROJECTS'], TEST_ORG, test_project)
    if os.path.exists(proj_data):
        shutil.rmtree(proj_data)

    namespace = Namespace.query.filter_by(name=TEST_ORG).first()
    mergin_user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    proj = Project.query.filter_by(namespace=DEFAULT_USER[0], name=test_project).first()
    project_transfer = ProjectTransfer(proj, namespace, mergin_user.id)
    db.session.add(project_transfer)

    org_reader = add_user('reader', 'reader')
    test_organisation.readers.append(org_reader.id)
    db.session.add(test_organisation)
    db.session.commit()

    login(client, 'reader', 'reader')
    data = {'name': test_project, 'transfer_permissions': True}
    resp = client.post(f'/v1/project/transfer/{project_transfer.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 403

    login(client, DEFAULT_USER[0], DEFAULT_USER[1])
    resp = client.post(f'/v1/project/transfer/{project_transfer.id}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    transferred_project = Project.query.filter_by(namespace=TEST_ORG, name=test_project).first()
    assert transferred_project
    assert transferred_project.creator.username == DEFAULT_USER[0]
    # mergin was owner even of original project
    for key in ['owners', 'readers', 'writers']:
        attr = getattr(transferred_project.access, key)
        assert len(attr) == 1 and attr[0] == transferred_project.creator.id
