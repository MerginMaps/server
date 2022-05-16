# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
from datetime import datetime, timedelta
import pytest
import json
from flask import url_for
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import desc
from sqlalchemy.orm.attributes import flag_modified
from unittest.mock import patch

from src.auth.models import User, UserProfile, LoginHistory
from src import db
from src.models.db_models import Namespace, Account, Project
from . import json_headers
from .utils import add_user, login_as_admin, login


@pytest.fixture(scope='function')
def client(app):
    client = app.test_client()
    return client


# login test: success, success with email login, invalid password, missing password, wrong headers
test_login_data = [
    ({'login': 'mergin', 'password': 'ilovemergin'}, json_headers, 200),
    ({'login': 'mergin@mergin.com', 'password': 'ilovemergin'}, json_headers, 200),
    ({'login': 'mergin', 'password': 'ilovemergi'}, json_headers, 401),
    ({'login': 'mergin'}, json_headers, 401),
    ({'login': 'mergin', 'password': 'ilovemergin'}, {}, 401),
]


@pytest.mark.parametrize("data,headers,expected", test_login_data)
def test_login(client, data, headers, expected):
    resp = client.post(url_for('auth.login'), data=json.dumps(data), headers=headers)
    assert resp.status_code == expected
    if expected == 200:
        login_history = LoginHistory.query.filter_by(username='mergin').order_by(desc(LoginHistory.timestamp)).first()
        assert login_history


def test_logout(client):
    login_as_admin(client)
    resp = client.get(url_for('auth.logout'))
    assert resp.status_code == 200


# user registration test
test_user_reg_data = [
    ('test', 'test@test.com', 200),  # success
    ('TesTUser', 'test@test.com', 200),  # test with upper case, but user is not exist
    ('TesTUser2', 'test2@test.com', 200),  # test with upper case, but user is not exist
    ('bob', 'test@test.com', 400),  # invalid (short) username
    ('test', 'test.com', 400),  # invalid email
    ('mergin', 'test@test.com', 400), # existing user
    ('MerGin', 'test@test.com', 400),  # test with upper case but mergin already exist
    ('  mergin  ', 'test@test.com', 400),  # test with blank spaces, but mergin user already exists
    ('XmerginX', ' test@test.com  ', 200),  # test with blank spaces, whitespace to be removed
    ('XmerginX', ' mergin@mergin.com  ', 400)  # test with blank spaces, but email already exists
]


@pytest.mark.parametrize("username,email,expected", test_user_reg_data)
def test_user_register(client, username, email, expected):
    login_as_admin(client)
    url = url_for('auth.register_user')
    resp = client.post(url, data=json.dumps({'username': username, 'email': email}), headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        user = User.query.filter_by(username=username).first()
        assert user
        assert user.active
        assert not user.verified_email
        ns = Namespace.query.filter_by(name=username).first()
        assert ns
        account = Account.query.filter_by(type='user', owner_id=user.id).first()
        assert account


@patch('src.celery.send_email_async.apply_async')
def test_confirm_email(send_email_mock, app, client):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps('mergin@mergin.com', salt=app.config['SECURITY_PASSWORD_SALT'])
    resp = client.get(url_for('auth.confirm_email', token=token))
    assert resp.status_code == 200
    assert b'Your email address has been verified.' in resp.data
    assert not send_email_mock.called

    user = User.query.filter_by(username='mergin').first()
    # test with old registered user
    user.verified_email = False
    user.profile.registration_date = datetime.utcnow() - timedelta(days=1)
    db.session.commit()
    resp = client.get(url_for('auth.confirm_email', token=token))
    assert resp.status_code == 200
    assert b'Your email address has been verified.' in resp.data
    assert not send_email_mock.called

    # try again with freshly registered user
    user.verified_email = False
    user.profile.registration_date = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    resp = client.get(url_for('auth.confirm_email', token=token))
    assert resp.status_code == 200
    assert b'Your email address has been verified.' in resp.data
    assert send_email_mock.called

    # try again
    resp = client.get(url_for('auth.confirm_email', token=token))
    assert resp.status_code == 200
    assert b'Your email address has been verified.' in resp.data

    # invalid token
    resp = client.get(url_for('auth.confirm_email', token='token'))
    assert resp.status_code == 400

    # not-existing user
    resp = client.get(url_for('auth.confirm_email',
                              token=serializer.dumps('test@mergin.com', salt=app.config['SECURITY_PASSWORD_SALT'])))
    assert resp.status_code == 404


def test_confirm_password(app, client):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps('mergin@mergin.com', salt=app.config['SECURITY_PASSWORD_SALT'])

    resp = client.get(url_for('auth.confirm_new_password', token=token))
    assert resp.status_code == 200
    assert b'Activate account' in resp.data

    form_data = {'password': 'ilovemergin#0', 'confirm': 'ilovemergin#0'}
    resp = client.post(url_for('auth.confirm_new_password', token=token), data=json.dumps(form_data), headers=json_headers)
    assert resp.status_code == 302

    # invalid token
    resp = client.get(url_for('auth.confirm_new_password', token='token'))
    assert resp.status_code == 400

    # not-existing user
    resp = client.get(url_for('auth.confirm_new_password',
                              token=serializer.dumps('test@mergin.com', salt=app.config['SECURITY_PASSWORD_SALT'])))
    assert resp.status_code == 404

    # add inactive user
    user = User(username='test', passwd='testuser', is_admin=True, email='test@mergin.com')
    user.active = False
    db.session.add(user)
    db.session.commit()
    resp = client.get(url_for('auth.confirm_new_password',
                              token=serializer.dumps('test@mergin.com', salt=app.config['SECURITY_PASSWORD_SALT'])))
    assert resp.status_code == 400


# reset password test: success, no email, not-existing user
test_reset_data = [
    ({'email': 'mergin@mergin.com'}, 200),
    ({'email': 'Mergin@mergin.com'}, 200),  # case insensitive
    ({}, 404),
    ({'email': 'test@mergin.com'}, 404)
]


@pytest.mark.parametrize("data,expected", test_reset_data)
def test_reset_password(client, data, expected):
    resp = client.post(url_for('auth.password_reset'), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        assert resp.json['success']


def test_change_password(client):
    username = 'user_test'
    old_password = 'user_password'
    new_password = 'Test#test'

    user = User(username=username, passwd=old_password, is_admin=True, email='user_test@mergin.com')
    user.active = True
    user.profile = UserProfile()
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        url_for('auth.login'),
        data=json.dumps({'login': username, 'password': old_password}),
        headers=json_headers
    )
    assert resp.status_code == 200

    # test old password incorrect
    resp = client.post(
        url_for('auth.change_password'),
        data=json.dumps(
            {'old_password': 'old_password_incorrect', 'password': new_password, 'confirm': new_password}),
        headers=json_headers
    )
    assert resp.status_code == 400

    # test correct old password
    resp = client.post(
        url_for('auth.change_password'),
        data=json.dumps(
            {'old_password': old_password, 'password': new_password, 'confirm': new_password}),
        headers=json_headers
    )
    assert resp.status_code == 200

    # test login with old password
    resp = client.post(
        url_for('auth.login'),
        data=json.dumps({'login': username, 'password': old_password}),
        headers=json_headers
    )
    assert resp.status_code == 401

    # test login with new password
    resp = client.post(
        url_for('auth.login'),
        data=json.dumps({'login': username, 'password': new_password}),
        headers=json_headers
    )
    assert resp.status_code == 200


def test_remove_user(client):
    login_as_admin(client)
    user = add_user('test', 'test')

    resp = client.delete(url_for('auth.delete_user', username=user.username))
    assert resp.status_code == 200
    assert resp.json['success']
    assert not User.query.filter_by(username='test').count()
    assert not Namespace.query.filter_by(name='test').count()

    resp = client.delete(url_for('auth.delete_user', username=user.username))
    assert resp.status_code == 404


def test_delete_account(client):
    username = 'user_test'
    password = 'user_password'
    user = add_user(username, password)
    ns = Namespace.query.filter_by(name=username).first()
    user_id = user.id

    # share project of default user
    project = Project.query.filter_by(namespace='mergin', name='test').first()
    assert project
    project.access.owners.append(user_id)
    project.access.writers.append(user_id)
    project.access.readers.append(user_id)
    db.session.add(project)
    flag_modified(project.access, 'owners')
    flag_modified(project.access, 'writers')
    flag_modified(project.access, 'readers')
    db.session.commit()
    assert user_id in project.access.owners

    login(client, username, password)

    # delete account
    resp = client.delete(url_for('auth.delete_account'))
    assert resp.status_code == 200
    assert resp.json['success']
    # check nothing is left in database
    user = User.query.filter_by(username=username).first()
    account = Account.query.filter_by(type='user', owner_id=user_id).first()
    assert not account
    assert not user
    ns = Namespace.query.filter_by(name=username).first()
    assert not ns
    assert user_id not in project.access.owners
    assert user_id not in project.access.writers
    assert user_id not in project.access.readers

    # try relogin but should be not found
    resp = client.post(
        url_for('auth.login'),
        data=json.dumps({'login': username, 'password': password}),
        headers=json_headers
    )
    assert resp.status_code == 401


def test_self_registration(client):
    resp = client.get(url_for('auth.self_register_user'))
    assert resp.status_code == 405

    form_data = {'username': 'test', 'email': 'test@test.com', 'password': 'Test#test', 'confirm': 'Test#test'}
    resp = client.post(url_for('auth.self_register_user'), data=json.dumps(form_data), headers=json_headers)
    assert resp.status_code == 200
    assert resp.json['username'] == 'test'


# self registrations: success, invalid username
test_self_registration_validation_data = [
    ({'username': 'test', 'email': 'test@test.com', 'password': 'Test#test', 'confirm': 'Test#test'}, json_headers, 200),
    ({'username': 'test!@%$', 'email': 'test@test.com', 'password': 'Test#test', 'confirm': 'Test#test'}, json_headers, 400)
]


@pytest.mark.parametrize("data,headers,expected", test_self_registration_validation_data)
def test_self_registration_validation(client, data, headers, expected):
    resp = client.post(url_for(
        'auth.self_register_user'), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected


# login test: success, success with email login, invalid password, missing password, wrong headers
test_api_login_data = [
    ({'login': 'mergin', 'password': 'ilovemergin'}, json_headers, 200),
    ({'login': 'mergin@mergin.com', 'password': 'ilovemergin'}, json_headers, 200),
    ({'login': 'mergin', 'password': 'ilovemergi'}, json_headers, 401),
    ({'login': 'mergin'}, json_headers, 400),
    ({'login': 'mergin', 'password': 'ilovemergin'}, {}, 415),
]


@pytest.mark.parametrize("data,headers,expected", test_api_login_data)
def test_api_login(client, data, headers, expected):
    resp = client.post('/v1/auth/login', data=json.dumps(data), headers=headers)
    assert resp.status_code == expected
    if expected == 200:
        login_history = LoginHistory.query.filter_by(username='mergin').order_by(desc(LoginHistory.timestamp)).first()
        assert login_history


def test_api_login_from_urllib(client):
    with patch('src.auth.models.get_user_agent') as mock:
        mock.return_value = "DB-sync/0.1"
        resp = client.post('/v1/auth/login', data=json.dumps({'login': 'mergin', 'password': 'ilovemergin'}), headers=json_headers)
        assert resp.status_code == 200
        login_history = LoginHistory.query.filter_by(username='mergin').order_by(desc(LoginHistory.timestamp)).first()
        assert not login_history


def test_api_user_profile(client):
    """ test public API endpoint to get user details """
    resp = client.get('/v1/user/mergin')
    assert resp.status_code == 401

    login_as_admin(client)
    user = User.query.filter_by(username="mergin").first()
    resp = client.get('/v1/user/mergin')
    assert resp.status_code == 200
    assert resp.json['username'] == 'mergin'
    assert resp.json['email'] == user.email
    assert resp.json['disk_usage'] == 0
    assert resp.json['storage_limit'] == 104857600

    # now check the profile of someone else
    resp = client.get('/v1/user/somebody_else')
    assert resp.status_code == 200
    assert resp.json['username'] == 'mergin'


# test_seeing_other_profile, invalid username
test_other_user_profile_data = [
    ({'username': 'test1', 'email': 'test@test.com', 'passwd': 'Test#test', 'is_admin': True}, True),
    ({'username': 'test2', 'email': 'test@test.com', 'passwd': 'Test#test', 'is_admin': False}, False)
]


def test_update_user(client):
    login_as_admin(client)
    user = User.query.filter_by(username='mergin').first()
    data = {"active": False}
    resp = client.post('/auth/user/{}'.format(user.username), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    assert not user.active

    user.is_admin = False
    db.session.add(user)
    db.session.commit()
    resp = client.post('/auth/user/{}'.format(user.id), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 403


def test_update_user_profile(client):
    login_as_admin(client)
    user = User.query.filter_by(username='mergin').first()
    user.verified_email = True

    user2 = User("test", "m@m.com", "testspass", False)
    db.session.add(user2)
    db.session.commit()
    assert user.profile.receive_notifications
    assert user.verified_email

    # update profile
    resp = client.post(
        url_for('auth.update_user_profile'),
        data=json.dumps(
            {
                'email': 'm@m.com'
            }
        ),
        headers=json_headers
    )
    assert resp.status_code == 400
    assert "Email already exists" in resp.json.get("email")

    # update profile
    resp = client.post(
        url_for('auth.update_user_profile'),
        data=json.dumps({
            'first_name': '  John',
            'last_name': 'Doe ',
            'email': 'john@doe.com '
        }),
        headers=json_headers
    )
    assert resp.status_code == 200
    assert user.email == 'john@doe.com'
    assert user.profile.first_name == 'John'
    assert user.profile.last_name == 'Doe'

    # update profile
    resp = client.post(
        url_for('auth.update_user_profile'),
        data=json.dumps(
            {
                'receive_notifications': False,
                'email': 'changed_email@mergin.co.uk'
            }
        ),
        headers=json_headers
    )
    assert resp.status_code == 200

    user = User.query.filter_by(username='mergin').first()
    assert not user.profile.receive_notifications
    assert not user.verified_email
    assert user.email == 'changed_email@mergin.co.uk'


def test_search_user(client):
    user = User.query.filter_by(username='mergin').first()

    resp = client.get('/auth/user/search')
    assert resp.status_code == 401

    login_as_admin(client)
    resp = client.get('/auth/user/search')
    assert resp.status_code == 200
    assert list(resp.json[0].keys()) == ['id', 'profile', 'username']

    add_user('fero.mrkva', 'test')
    add_user('palomrmrkva', 'test')
    add_user('mrkvajozef', 'test')
    resp = client.get('/auth/user/search?like=erg')
    assert 'mer' in resp.json[0]['username']

    resp = client.get('/auth/user/search?like=mrk')
    assert 'palomrmrkva' in resp.json[2]['username']
    assert 'mrkvajozef' in resp.json[1]['username']
    assert 'fero.mrkva' in resp.json[0]['username']
    assert 3 == len(resp.json)

    resp = client.get('/auth/user/search?like=.mrk')
    assert 'fero.mrkva' in resp.json[0]['username']
    assert 1 == len(resp.json)


    resp = client.get('/auth/user/search?id={}'.format(user.id))
    assert resp.json[0]['username'] == user.username

    resp = client.get('/auth/user/search?names={}'.format(user.username))
    assert resp.json[0]['username'] == user.username

    # no such user
    resp = client.get('/auth/user/search?like=test')
    assert not resp.json

    # invalid query par
    resp = client.get('/auth/user/search?id=1,a')
    assert resp.json


def test_get_accounts(client):
    resp = client.get(url_for('account.list_accounts', type='user'))
    assert resp.status_code == 401

    login_as_admin(client)
    resp = client.get(url_for('account.list_accounts', type='user'))

    assert resp.status_code == 200
    assert resp.json['total'] == 1
    account = resp.json['accounts'][0]
    assert account['type'] == 'user'
    assert account['name'] == 'mergin'

    # filter by type
    resp = client.get(url_for('account.list_accounts', type='foo'))
    assert resp.status_code == 400

    resp = client.get(url_for('account.list_accounts', type='organisation'))
    assert resp.status_code == 200
    assert resp.json['total'] == 0

    resp = client.get(url_for('account.list_accounts', type='user', page=2))
    assert resp.status_code == 404

    resp = client.get(url_for('account.list_accounts', type='user', name='merg'))
    assert resp.status_code == 200
    assert resp.json['total'] == 1

    resp = client.get(url_for('account.list_accounts', type='user', name='foo'))
    assert resp.status_code == 200
    assert resp.json['total'] == 0

    add_user('foo', 'bar')
    resp = client.get(url_for('account.list_accounts', type='user', name='foo'))
    assert resp.status_code == 200
    assert resp.json['total'] == 1

    resp = client.get(url_for('account.list_accounts', type='user', order_by='name', descending='true'))
    assert resp.status_code == 200
    assert resp.json['accounts'][0]['name'] == 'mergin'
    assert resp.json['accounts'][1]['name'] == 'foo'
