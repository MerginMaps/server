# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import json
import os
import shutil
import pytest
from datetime import timedelta
from flask import url_for
from src.models.db_models import Namespace, Project, Account
from src.organisation import Organisation, OrganisationInvitation
from src.auth.models import User
from src import db

from .utils import add_user, create_project, DateTimeEncoder, login
from .test_project_controller import _get_changes
from . import json_headers, TEST_ORG, test_project_dir, DEFAULT_USER

add_organisation_data = [
    ({"name": TEST_ORG}, 201),
    ({"name": TEST_ORG, "description": "test"}, 201),
    ({"description": "test"}, 400),  # missing required field
    ({"name": "#$&^*"}, 400)  # invalid field
]


@pytest.mark.parametrize("data,expected", add_organisation_data)
def test_create_organisation(client, data, expected):
    owner = User.query.filter_by(username='mergin').first()
    resp = client.post(url_for('organisation.create_organisation'), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 201:
        assert Organisation.query.filter_by(name=TEST_ORG).count() == 1
        assert Namespace.query.filter_by(name=TEST_ORG).count() == 1
        org = Organisation.query.filter_by(name=TEST_ORG).first()
        assert org.owners == [owner.id]
        # call user profile endpoint to check its organisations
        resp = client.get('/v1/user/owner')
        assert resp.json['organisations'][org.name] == 'owner'


def test_add_existing_org(client, test_organisation):
    resp = client.post(url_for('organisation.create_organisation'), data=json.dumps({"name": TEST_ORG}), headers=json_headers)
    assert resp.status_code == 409
    resp = client.post(url_for('organisation.create_organisation'), data=json.dumps({"name": TEST_ORG.upper()}), headers=json_headers)
    assert resp.status_code == 409

    # test user with the same name as organisation can not be created
    resp = client.post(
        url_for('auth.register_user'),
        data=json.dumps({'username': TEST_ORG, 'email': 'test@test.com'}),
        headers=json_headers
    )
    assert resp.status_code == 400


def test_free_orgs_limit(client, test_organisation):
    url = url_for('organisation.create_organisation')
    client.post(url, data=json.dumps({"name": "org2"}), headers=json_headers)
    Namespace.query.filter_by(name="org2").update({"storage": 0})
    client.post(url, data=json.dumps({"name": "org3"}), headers=json_headers)
    Namespace.query.filter_by(name="org3").update({"storage": 0})
    db.session.commit()
    resp = client.post(url, data=json.dumps({"name": "org4"}), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json["detail"] == "Too many free organisations"


test_organisation_data = [
    ('foo', 404),
    (TEST_ORG, 200),
]


def test_list_organisations(client, test_organisation):
    user = add_user('bob', 'foo')
    login(client, 'bob', 'foo')
    resp = client.get(url_for('organisation.get_organisations'))
    assert resp.status_code == 200
    assert len(json.loads(resp.data)) == 0

    org = Organisation(name='bob-org', creator_id=user.id)
    db.session.add(org)
    db.session.commit()

    resp = client.get(url_for('organisation.get_organisations'))
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data) == 1
    assert resp_data[0]["name"] == 'bob-org'

    # login as someone else (even admin)
    login(client, 'mergin', 'ilovemergin')
    resp = client.get(url_for('organisation.get_organisations'))
    assert resp.status_code == 200
    assert len(json.loads(resp.data)) == 1
    assert json.loads(resp.data)[0]["name"] != 'bob-org'


@pytest.mark.parametrize("name, status_code", test_organisation_data)
def test_get_organisation(client, test_organisation, name, status_code):
    resp = client.get(url_for('organisation.get_organisation_by_name', name=name))
    assert resp.status_code == status_code
    if resp.status_code == 200:
        resp_data = json.loads(resp.data)
        assert resp_data["name"] == name
        assert DEFAULT_USER[0] in resp_data["owners"]


def test_get_org_by_non_member(client, test_organisation):
    add_user("test", "test")
    login(client, "test", "test")
    resp = client.get(url_for('organisation.get_organisation_by_name', name=TEST_ORG))
    assert resp.status_code == 403


def test_delete_organisation(client, test_organisation):
    url = url_for('organisation.delete_organisation', name=TEST_ORG)
    login(client, "admin", "admin")
    resp = client.delete(url)
    assert resp.status_code == 403

    # create some project
    owner = User.query.filter_by(username="owner").first()
    project = create_project("test1", test_organisation.name, owner)
    project_dir = project.storage.project_dir
    assert os.path.exists(project_dir)

    login(client, "owner", "owner")
    resp = client.delete(url)
    assert resp.status_code == 200
    assert not Organisation.query.filter_by(name=TEST_ORG).count()
    assert not Namespace.query.filter_by(name=TEST_ORG).count()
    assert not Project.query.filter_by(namespace=TEST_ORG).count()
    assert not os.path.exists(project_dir)


def test_update_org(client, test_organisation):
    url = url_for('organisation.update_organisation', name=TEST_ORG)
    # login as owner
    login(client, "owner", "owner")
    data = {"description": "Foo"}

    resp = client.patch(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    org = Organisation.query.filter_by(name=TEST_ORG).first()
    assert org.description == "Foo"

    # login with not-privileged user
    login(client, "admin", "admin")
    resp = client.patch(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 403


def test_update_members(client, test_organisation):
    url = url_for('organisation.update_access', name=TEST_ORG)
    new_writer = add_user("writer", "writer")
    login(client, "writer", "writer")
    # check no access
    resp = client.get(url_for('organisation.get_organisations', username='writer'))
    assert not json.loads(resp.data)

    # login with as admin
    login(client, "admin", "admin")
    data = {
        "owners": ["owner"],
        "admins": ["admin", "owner"],
        "writers": ["admin", "writer"],
        "readers": ["admin", "writer"]
    }

    resp = client.patch(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    org = Organisation.query.filter_by(name=TEST_ORG).first()
    assert new_writer.id in org.writers
    assert new_writer.id in org.readers

    # login with not-privileged user
    login(client, "writer", "writer")
    resp = client.patch(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 403

    # try to remove all members
    login(client, "owner", "owner")
    data = {"owners": [], "admins": [], "writers": [], "readers": []}
    resp = client.patch(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400


@pytest.fixture(scope='function')
def test_invitation(test_organisation):
    # default organisation
    add_user("user", "user")
    add_user("user1", "user1")

    invitation = OrganisationInvitation(TEST_ORG, 'user', 'admin')
    db.session.add(invitation)
    db.session.commit()


create_invitation_data = [
    ({"username": 'user1', "org_name": TEST_ORG, "role": 'admin'}, 'admin', 'admin', 201),  # admin create invitation
    ({"username": 'user1', "org_name": TEST_ORG, "role": 'admin'}, 'owner', 'owner', 201),  # owner create invitation
    ({"username": 'user1', "org_name": TEST_ORG, "role": 'admin'}, 'user', 'user', 403),  # user can't create invitation
    ({"username": 'user', "org_name": TEST_ORG, "role": 'admin'}, 'admin', 'admin', 409),  # already exist
    ({"username": 'user', "org_name": "org", "role": 'admin'}, 'admin', 'admin', 404),  # organisation not found
    ({"username": 'user_test', "org_name": TEST_ORG, "role": 'admin'}, 'admin', 'admin', 404),  # user not found
    ({"username": 'user', "org_name": TEST_ORG, "role": 'test'}, 'admin', 'admin', 400),  # wrong role
]


@pytest.mark.parametrize("data, username, password, expected", create_invitation_data)
def test_create_invitation(client, test_invitation, data, username, password, expected):
    login(client, username, password)
    url = url_for('organisation.create_invitation')
    resp = client.post(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 201:
        login(client, "user1", "user1")
        url = url_for('organisation.get_invitations', type="user", name="user1")
        resp = client.get(url, headers=json_headers)
        assert resp.status_code == 200
        assert len(resp.json) == 1
        invitation = resp.json[0]
        for key, value in data.items():
            assert key in invitation.keys()
            assert value == invitation[key]


get_invitation_data = [
    ('user', 1, 200),  # user can see invitation 1 (target)
    ('admin', 1, 200),  # admin can see invitation 1 (admin of org)
    ('user1', 1, 403),  # user1 can't see invitation 1
    ('user', 2, 404),  # invitation 1 is not exist
]


@pytest.mark.parametrize("user, id, expected", get_invitation_data)
def test_get_invitation(client, test_invitation, user, id, expected):
    url = url_for('organisation.get_invitation', id=id)
    login(client, user, user)
    resp = client.get(url, headers=json_headers)
    assert resp.status_code == expected


@pytest.mark.parametrize("user, id, expected", get_invitation_data)
def test_delete_invitation(client, test_invitation, user, id, expected):
    url = url_for('organisation.delete_invitation', id=id)
    login(client, user, user)
    resp = client.delete(url, headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        url = url_for('organisation.get_invitation', id=id)
        resp = client.get(url, headers=json_headers)
        assert resp.status_code == 404


test_accept_invitation_data = [
    ('user', 1, False, 200),  # user can accept 1 (target)
    ('user', 1, True, 400),  # user can accept 1 (target) but already expired
    ('admin', 1, False, 403),  # admin can see invitation 1 (admin of org) but not the target
    ('user1', 1, False, 403),  # user1 can't accept invitation 1
    ('user', 2, False, 404),  # invitation 1 is not exist
]


@pytest.mark.parametrize("user, id, expired, expected", test_accept_invitation_data)
def test_accept_invitation(client, test_invitation, user, id, expired, expected):
    # if expired:
    if expired:
        invitation = OrganisationInvitation.query.first()
        invitation.expire = invitation.expire - timedelta(
            seconds=client.application.config['ORGANISATION_INVITATION_EXPIRATION'])
        db.session.add(invitation)
        db.session.commit()

    url = url_for('organisation.accept_invitation', id=id)
    login(client, user, user)
    resp = client.post(url, headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        organisation = Organisation.query.first()
        user = User.query.filter_by(username=user).first()
        assert user.id in organisation.admins


def test_upload_to_free_org(client, diff_project, test_organisation):
    # clean up
    proj_data = os.path.join(client.application.config['LOCAL_PROJECTS'], TEST_ORG, 'empty')
    if os.path.exists(proj_data):
        shutil.rmtree(proj_data)

    login(client, 'mergin', 'ilovemergin')
    # try clone to free organisation
    data = {
        'namespace': TEST_ORG,
        'project': 'clone'
    }
    resp = client.post(f'/v1/project/clone/{DEFAULT_USER[0]}/test', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400
    assert 'Disk quota reached' in resp.json['detail']

    # create empty project and then push to
    data = {'name': 'empty'}
    resp = client.post(f'/v1/project/{TEST_ORG}', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200

    data = {'version': 'v0', 'changes': _get_changes(test_project_dir)}
    resp = client.post(f'/v1/project/push/{TEST_ORG}/empty', data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 400
    assert 'You have reached a data limit' in resp.json['detail']


def test_fetch_organisation_projects(client, test_organisation):
    login(client, 'mergin', 'ilovemergin')
    resp = client.post(f'/v1/project/{TEST_ORG}', data=json.dumps({"name": "org_project"}), headers=json_headers)
    assert resp.status_code == 200
    resp = client.post(f'/v1/project/{DEFAULT_USER[0]}', data=json.dumps({"name": "usr_project"}), headers=json_headers)
    assert resp.status_code == 200
    url = '/v1/project?flag=shared'
    resp = client.get(url, headers=json_headers)
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data) == 1

    login(client, "admin", "admin")
    url = '/v1/project?flag=shared'
    resp = client.get(url, headers=json_headers)
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data) == 1

    add_user("random", "random")
    login(client, "random", "random")
    url = '/v1/project?flag=shared'
    resp = client.get(url, headers=json_headers)
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert not len(resp_data)
