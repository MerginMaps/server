# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime, timedelta
import time
import pytest
import json
from flask import url_for
from sqlalchemy import desc
from unittest.mock import patch

from ..auth.forms import ResetPasswordForm
from ..auth.app import generate_confirmation_token, confirm_token
from ..auth.models import User, UserProfile, LoginHistory
from ..auth.tasks import anonymize_removed_users
from ..app import db
from ..sync.models import Project, ProjectRole
from . import (
    test_workspace_id,
    json_headers,
    DEFAULT_USER,
    test_workspace_name,
    test_project,
)
from .utils import (
    add_user,
    create_project,
    create_workspace,
    login_as_admin,
    login,
    upload_file_to_project,
)


@pytest.fixture(scope="function")
def client(app):
    client = app.test_client()
    return client


# login tests: success, success with trailing space, success with email login, invalid password, missing password, wrong headers
test_login_data = [
    ({"login": "mergin", "password": "ilovemergin"}, json_headers, 200),
    ({"login": "mergin  ", "password": "ilovemergin"}, json_headers, 200),
    ({"login": "mergin@mergin.com", "password": "ilovemergin"}, json_headers, 200),
    (
        {"login": "mergin", "password": "ilovemergin"},
        {**json_headers, "X-Device-Id": None},
        200,
    ),
    ({"login": "mergin", "password": "ilovemergi"}, json_headers, 401),
    ({"login": "mergin"}, json_headers, 401),
    ({"login": "mergin", "password": "ilovemergin"}, {}, 415),
    # case insensitive login
    ({"login": "merGIN", "password": "ilovemergin"}, json_headers, 200),
    ({"login": "merGIN@MERgin.com", "password": "ilovemergin"}, json_headers, 200),
]


@pytest.mark.parametrize("data,headers,expected", test_login_data)
def test_login(client, data, headers, expected):
    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps(data),
        headers=headers,
    )
    assert resp.status_code == expected
    if expected == 200:
        user = User.query.filter_by(username=DEFAULT_USER[0]).first()
        login_history = (
            LoginHistory.query.filter_by(user_id=user.id)
            .order_by(desc(LoginHistory.timestamp))
            .first()
        )
        assert login_history
        assert login_history.device_id == str(headers.get("X-Device-Id"))


def test_logout(client):
    login_as_admin(client)
    resp = client.get(url_for("/.mergin_auth_controller_logout"))
    assert resp.status_code == 200


# user registration tests
test_user_reg_data = [
    ("test@test.com", "#pwd1234", 201),  # success
    (
        "test@test.com",
        "#pwd1234",
        201,
    ),  # tests with upper case, but user does not exist
    (
        "test2@test.com",
        "#pwd1234",
        201,
    ),  # tests with upper case, but user does not exist
    ("test.com", "#pwd1234", 400),  # invalid email
    ("admin@example.com", "#pwd1234", 201),  # some random admin with diff email,
    (
        " tests@test.com  ",
        "#pwd1234",
        201,
    ),  # tests with blank spaces, whitespace to be removed
    (
        " mergin@mergin.com  ",
        "#pwd1234",
        400,
    ),  # tests with blank spaces, but email already exists
    (
        " merGIN@mergin.com  ",
        "#pwd1234",
        400,
    ),  # tests with upper case, but email already exists
    (" mergin@mergin.com  ", "#pwd123", 400),  # invalid password
    ("verylonglonglonglonglonglonglongemail@example.com", "#pwd1234", 201),
    ("us.er@mergin.com", "#pwd1234", 201),  # dot is allowed
    ("us er@mergin.com", "#pwd1234", 400),  # space is disallowed
]


@pytest.mark.parametrize("email,pwd,expected", test_user_reg_data)
def test_user_register(client, email, pwd, expected):
    login_as_admin(client)
    url = url_for("/.mergin_auth_controller_register_user")
    data = {"email": email, "password": pwd, "confirm": pwd}
    resp = client.post(url, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 201:
        user = User.query.filter_by(email=email.strip()).first()
        assert user
        assert user.active
        assert not user.verified_email  # awaits user confirmation


def test_confirm_email(app, client):
    user = User.query.filter_by(username="mergin").first()
    token = generate_confirmation_token(
        app, user.email, app.config["SECURITY_EMAIL_SALT"]
    )
    user.verified_email = False
    db.session.commit()

    # verify token can't be used in different context
    resp = client.post(
        url_for("/.mergin_auth_controller_confirm_new_password", token=token),
        json={"password": "ilovemergin#0", "confirm": "ilovemergin#0"},
    )
    assert resp.status_code == 400

    resp = client.post(url_for("/.mergin_auth_controller_confirm_email", token=token))
    assert resp.status_code == 200

    # try again
    resp = client.post(url_for("/.mergin_auth_controller_confirm_email", token=token))
    assert resp.status_code == 200

    # invalid token
    resp = client.post(url_for("/.mergin_auth_controller_confirm_email", token="token"))
    assert resp.status_code == 400

    # not-existing user
    resp = client.post(
        url_for(
            "/.mergin_auth_controller_confirm_email",
            token=generate_confirmation_token(
                app, "tests@mergin.com", app.config["SECURITY_EMAIL_SALT"]
            ),
        )
    )
    assert resp.status_code == 404

    # test expired token
    token = generate_confirmation_token(
        app, user.email, app.config["SECURITY_EMAIL_SALT"]
    )
    time.sleep(2)
    assert not confirm_token(
        token=token, expiration=1, salt=app.config["SECURITY_EMAIL_SALT"]
    )


def test_confirm_password(app, client):
    user = User.query.filter_by(username="mergin").first()
    token = generate_confirmation_token(
        app, user.email, app.config["SECURITY_PASSWORD_SALT"]
    )

    form_data = {"password": "ilovemergin#0", "confirm": "ilovemergin#0"}

    # verify token can't be used in different context
    resp = client.post(url_for("/.mergin_auth_controller_confirm_email", token=token))
    assert resp.status_code == 400

    resp = client.post(
        url_for("/.mergin_auth_controller_confirm_new_password", token=token),
        data=json.dumps(form_data),
        headers=json_headers,
    )
    assert resp.status_code == 200

    # invalid token
    resp = client.post(
        url_for("/.mergin_auth_controller_confirm_new_password", token="token"),
        data=json.dumps(form_data),
        headers=json_headers,
    )
    assert resp.status_code == 400

    # not-existing user
    resp = client.post(
        url_for(
            "/.mergin_auth_controller_confirm_new_password",
            token=generate_confirmation_token(
                app, "tests@mergin.com", app.config["SECURITY_PASSWORD_SALT"]
            ),
        ),
        data=json.dumps(form_data),
        headers=json_headers,
    )
    assert resp.status_code == 404

    # add inactive user
    user = User(
        username="tests", passwd="testuser", is_admin=True, email="tests@mergin.com"
    )
    user.active = False
    db.session.add(user)
    db.session.commit()
    resp = client.post(
        url_for(
            "/.mergin_auth_controller_confirm_new_password",
            token=generate_confirmation_token(
                app, "tests@mergin.com", app.config["SECURITY_PASSWORD_SALT"]
            ),
        )
    )
    assert resp.status_code == 400


# reset password tests: success, no email, not-existing user
test_reset_data = [
    ({"email": "mergin@mergin.com"}, 200),
    ({"email": "Mergin@mergin.com"}, 200),  # case insensitive
    ({}, 400),
    ({"email": "tests@mergin.com"}, 404),
]


@pytest.mark.parametrize("data,expected", test_reset_data)
def test_reset_password(client, data, expected):
    resp = client.post(
        url_for("/.mergin_auth_controller_password_reset"),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == expected


def test_change_password(client):
    username = "user_test"
    old_password = "user_password"
    new_password = "Test#tests"

    user = User(
        username=username,
        passwd=old_password,
        is_admin=True,
        email="user_test@mergin.com",
    )
    user.active = True
    user.profile = UserProfile()
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": username, "password": old_password}),
        headers=json_headers,
    )
    assert resp.status_code == 200

    # tests old password incorrect
    resp = client.post(
        url_for("/.mergin_auth_controller_change_password"),
        data=json.dumps(
            {
                "old_password": "old_password_incorrect",
                "password": new_password,
                "confirm": new_password,
            }
        ),
        headers=json_headers,
    )
    assert resp.status_code == 400

    # tests correct old password
    resp = client.post(
        url_for("/.mergin_auth_controller_change_password"),
        data=json.dumps(
            {
                "old_password": old_password,
                "password": new_password,
                "confirm": new_password,
            }
        ),
        headers=json_headers,
    )
    assert resp.status_code == 200

    # tests login with old password
    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": username, "password": old_password}),
        headers=json_headers,
    )
    assert resp.status_code == 401

    # tests login with new password
    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": username, "password": new_password}),
        headers=json_headers,
    )
    assert resp.status_code == 200


def test_remove_user(client):
    """Test force removal of user by admin"""
    login_as_admin(client)
    user = add_user("tests", "tests")

    resp = client.delete(
        url_for("/.mergin_auth_controller_delete_user", username=user.username)
    )
    assert resp.status_code == 204
    assert not User.query.filter_by(username="tests").count()
    assert user.username.startswith("deleted_") and not user.active

    resp = client.delete(
        url_for("/.mergin_auth_controller_delete_user", username="tests")
    )
    assert resp.status_code == 404

    # try to login but user should not be found
    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": "tests", "password": "tests"}),
        headers=json_headers,
    )
    assert resp.status_code == 401


# login tests: success, success with email login, invalid password, missing password, wrong headers
test_api_login_data = [
    ({"login": "mergin", "password": "ilovemergin"}, json_headers, 200),
    ({"login": "mergin@mergin.com", "password": "ilovemergin"}, json_headers, 200),
    ({"login": "mergin", "password": "ilovemergi"}, json_headers, 401),
    ({"login": "mergin"}, json_headers, 400),
    ({"login": "mergin", "password": "ilovemergin"}, {}, 415),
]


@pytest.mark.parametrize("data,headers,expected", test_api_login_data)
def test_api_login(client, data, headers, expected):
    resp = client.post("/v1/auth/login", data=json.dumps(data), headers=headers)
    assert resp.status_code == expected
    if expected == 200:
        user = User.query.filter_by(username=DEFAULT_USER[0]).first()
        login_history = (
            LoginHistory.query.filter_by(user_id=user.id)
            .order_by(desc(LoginHistory.timestamp))
            .first()
        )
        assert login_history


def test_api_login_from_urllib(client):
    with patch("mergin.auth.models.get_user_agent") as mock:
        mock.return_value = "DB-sync/0.1"
        resp = client.post(
            "/v1/auth/login",
            data=json.dumps({"login": "mergin", "password": "ilovemergin"}),
            headers=json_headers,
        )
        assert resp.status_code == 200
        user = User.query.filter_by(username=DEFAULT_USER[0]).first()
        login_history = (
            LoginHistory.query.filter_by(user_id=user.id)
            .order_by(desc(LoginHistory.timestamp))
            .first()
        )
        assert not login_history


def test_api_user_profile(client):
    """tests public API endpoint to get user details"""
    resp = client.get("/v1/user/mergin")
    assert resp.status_code == 401

    login_as_admin(client)
    resp = client.get("/v1/user/mergin")
    assert resp.status_code == 200
    assert resp.json["username"] == "mergin"
    assert resp.json["organisations"] == {
        test_workspace_name: "owner"
    }  # default workspace
    # tests legacy properties are in response
    for key in ["storage", "storage_limit", "disk_usage"]:
        assert key in resp.json


def test_update_user(client):
    login_as_admin(client)
    user = User.query.filter_by(username="mergin").first()
    data = {"active": True, "is_admin": True}
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert user.active
    assert user.is_admin

    client.application.config["ENABLE_SUPERADMIN_ASSIGNMENT"] = False
    data = {"active": False, "is_admin": False}
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 400
    assert user.active
    data = {"active": False}
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert not user.active

    client.application.config["ENABLE_SUPERADMIN_ASSIGNMENT"] = True
    user.is_admin = False
    db.session.add(user)
    db.session.commit()
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 403


def test_update_user_profile(client):
    login_as_admin(client)
    user = User.query.filter_by(username="mergin").first()
    user.verified_email = True

    user2 = User("tests", "m@m.com", "testspass", False)
    db.session.add(user2)
    db.session.commit()
    assert user.profile.receive_notifications
    assert user.verified_email

    # update profile
    resp = client.post(
        url_for("/.mergin_auth_controller_update_user_profile"),
        data=json.dumps({"email": "m@m.com"}),
        headers=json_headers,
    )
    assert resp.status_code == 400
    assert "Email already exists" in resp.json.get("email")

    # update profile
    resp = client.post(
        url_for("/.mergin_auth_controller_update_user_profile"),
        data=json.dumps(
            {"first_name": "  John", "last_name": "Doe ", "email": "john@doe.com "}
        ),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert user.email == "john@doe.com"
    assert user.profile.first_name == "John"
    assert user.profile.last_name == "Doe"

    # update profile
    resp = client.post(
        url_for("/.mergin_auth_controller_update_user_profile"),
        data=json.dumps(
            {"receive_notifications": False, "email": "changed_email@mergin.co.uk"}
        ),
        headers=json_headers,
    )
    assert resp.status_code == 200

    user = User.query.filter_by(username="mergin").first()
    assert not user.profile.receive_notifications
    assert not user.verified_email
    assert user.email == "changed_email@mergin.co.uk"

    #  do not allow to update sso user
    sso_user = add_user("sso_user", "sso")
    login(client, sso_user.username, "sso")
    sso_user.passwd = None
    db.session.add(sso_user)
    db.session.commit()
    resp = client.post(
        url_for("/.mergin_auth_controller_update_user_profile"),
        data=json.dumps({"email": "changed_email@sso.co.uk"}),
        headers=json_headers,
    )
    assert resp.status_code == 403


def test_search_user(client):
    user = User.query.filter_by(username="mergin").first()

    # query without workspace
    assert client.get("/app/auth/user/search").status_code == 400

    # anonymous user
    assert client.get("/app/auth/user/search?namespace=tests").status_code == 401

    login_as_admin(client)
    # not existing workspace
    assert client.get("/app/auth/user/search?namespace=tests").status_code == 404

    ws = client.application.config["GLOBAL_WORKSPACE"]
    # no query params to filter users
    resp = client.get(f"/app/auth/user/search?namespace={ws}")
    assert resp.status_code == 200
    assert len(resp.json) == 0

    add_user("fero.mrkva", "tests")
    add_user("palomrmrkva", "tests")
    add_user("mrkvajozef", "tests")
    add_user("mrk", "tests")
    url = f"/app/auth/user/search?namespace={ws}"
    resp = client.get(url + "&like=erg")
    assert "mer" in resp.json[0]["username"]
    assert set(resp.json[0].keys()) == {"id", "name", "username", "email"}

    # search by email
    resp = client.get(url + f"&like={user.email}")
    assert resp.json[0]["username"] == "mergin"
    resp = client.get(url + "&like=@mergin.com")
    assert len(resp.json) == 5  # all users since this is default domain

    # all search levels (1. exact 2. prefix, 3. word start 4. anywhere)
    resp = client.get(url + "&like=mrk")
    assert "mrk" in resp.json[0]["username"]
    assert "mrkvajozef" in resp.json[1]["username"]
    assert "fero.mrkva" in resp.json[2]["username"]
    assert "palomrmrkva" in resp.json[3]["username"]
    assert 4 == len(resp.json)

    # search levels without exact (1. prefix, 2. word start 3. anywhere)
    resp = client.get(url + "&like=mrkv")
    assert "mrkvajozef" in resp.json[0]["username"]
    assert "fero.mrkva" in resp.json[1]["username"]
    assert "palomrmrkva" in resp.json[2]["username"]
    assert 3 == len(resp.json)

    # just exact search level
    resp = client.get(url + "&like=mrkvajozef")
    assert "mrkvajozef" in resp.json[0]["username"]
    assert 1 == len(resp.json)

    # just prefix search level
    resp = client.get(url + "&like=palo")
    assert "palomrmrkva" in resp.json[0]["username"]
    assert 1 == len(resp.json)

    # just word start search level
    resp = client.get(url + "&like=.mrk")
    assert "fero.mrkva" in resp.json[0]["username"]
    assert 1 == len(resp.json)

    # just anywhere search level
    resp = client.get(url + "&like=kva")
    assert "fero.mrkva" in resp.json[0]["username"]
    assert "mrkvajozef" in resp.json[1]["username"]
    assert "palomrmrkva" in resp.json[2]["username"]
    assert 3 == len(resp.json)

    resp = client.get(url + f"&id={user.id}")
    assert resp.json[0]["username"] == user.username

    resp = client.get(url + f"&names={user.username}")
    assert resp.json[0]["username"] == user.username

    # no such user
    resp = client.get(url + "&like=tests")
    assert len(resp.json) == 0

    # invalid query par
    resp = client.get(url + f"&id=1,a")
    assert len(resp.json) == 0


def test_csrf_refresh_token(client):
    resp = client.get(url_for("/.mergin_auth_controller_refresh_csrf_token"))
    assert resp.status_code == 401

    login_as_admin(client)
    resp = client.get(url_for("/.mergin_auth_controller_refresh_csrf_token"))
    assert resp.json["csrf"]


def test_close_user_account(client):
    """Test closing user account via public API call and admin actions to enable/ban user"""
    username = "alice"
    user = add_user(username, "pwd")
    login(client, username, "pwd")
    # user closes account
    resp = client.delete("/v1/user")
    assert resp.status_code == 204
    assert user.active is False
    assert user.inactive_since
    # login is not possible
    assert (
        client.post(
            url_for("/.mergin_auth_controller_login"),
            data=json.dumps({"login": user.username, "password": "pwd"}),
            headers=json_headers,
        ).status_code
        == 401
    )

    login_as_admin(client)
    # email is still occupied
    data = {
        "username": user.username + "_new",
        "email": user.email,
        "password": "Pwd123###",
        "confirm": "Pwd123###",
    }
    assert (
        client.post(
            url_for("/.mergin_auth_controller_register_user"),
            data=json.dumps(data),
            headers=json_headers,
        ).status_code
        == 400
    )

    resp = client.get(
        url_for("/.mergin_auth_controller_get_user", username=user.username)
    )
    assert resp.json["scheduled_removal"]

    # admin can re-enable account
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps({"active": True}),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert user.active is True
    assert not user.inactive_since
    # admin can ban user
    resp = client.patch(
        url_for("/.mergin_auth_controller_update_user", username=user.username),
        data=json.dumps({"active": False}),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert user.active is False
    assert not user.inactive_since
    # admin can force delete user
    resp = client.delete(
        url_for("/.mergin_auth_controller_delete_user", username=username)
    )
    assert resp.status_code == 204
    assert not User.query.filter_by(username=username).first()
    assert user.username.startswith("deleted_") and not user.active

    user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    # check default project
    project = Project.query.filter_by(workspace_id=test_workspace_id).first()
    assert project.get_role(user.id) is ProjectRole.OWNER

    resp = client.delete("/v1/user")
    assert resp.status_code == 204
    user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    # tests only basic functionality - inactivate user and project
    # more complex testing is done in close mergin account tests case
    assert not user.active
    assert user.inactive_since
    assert (
        project.project_users == []
    )  # project will be removed by cron job, but is not accessible

    # login should fail now
    data = {"login": DEFAULT_USER[0], "password": DEFAULT_USER[1]}
    resp = client.post("/v1/auth/login", data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 401

    # mimic expiry, call celery job and check user is gone
    user.inactive_since = datetime.today() - timedelta(
        client.application.config["ACCOUNT_EXPIRATION"] + 1
    )
    db.session.commit()
    users_number = User.query.count()
    anonymize_removed_users()
    assert not User.query.filter_by(username=DEFAULT_USER[0]).first()
    assert User.query.count() == users_number


def test_paginate_users(client):
    """Test admin paginate user endpoint"""
    add_user("alice", "tests")  # 2
    add_user("bob", "tests")  # 3
    # username starts 'deleted_' but is active -> should be listed
    deleted_active = add_user("deleted_active", "tests")  # 4
    # user is inactive but username does not start 'deleted_' -> should be listed
    user_inactive = add_user("user_inactive", "user_inactive")  # 5
    user_inactive.active = False
    db.session.commit()
    # username starts 'deleted_' and is inactive -> should not be listed
    deleted_inactive = add_user("deleted_inactive", "deleted_inactive")  # not listed
    deleted_inactive.active = False
    db.session.commit()
    login(client, *DEFAULT_USER)
    url = "/app/admin/users?page=1&per_page=10"
    # get 5 users (default + 5 new added - 1 deleted & inactive)
    resp = client.get(url)
    list_of_usernames = [user["username"] for user in resp.json["items"]]
    assert resp.json["count"] == 5
    assert resp.json["items"][0]["username"] == "mergin"
    assert user_inactive.username in list_of_usernames
    assert deleted_active.username in list_of_usernames
    assert deleted_inactive.username not in list_of_usernames
    # order by username
    resp = client.get(url + "&order_by=username")
    assert resp.json["count"] == 5
    assert resp.json["items"][0]["username"] == "alice"
    # exact match with username
    resp = client.get(url + "&like=bob")
    assert resp.json["count"] == 1
    assert resp.json["items"][0]["username"] == "bob"
    # ilike search with email
    resp = client.get(url + "&like=@mergin.com")
    assert resp.json["count"] == 5
    # exact search by email
    resp = client.get(url + "&like=alice@mergin.com")
    assert resp.json["count"] == 1
    assert resp.json["items"][0]["username"] == "alice"
    # invalid paging
    assert client.get("/app/admin/users?page=2&per_page=10").status_code == 404


def test_user_info(client):
    """Test user profile of logged-in user"""
    login(client, *DEFAULT_USER)
    resp = client.get("/v1/user/profile")
    assert resp.json["username"] == DEFAULT_USER[0]
    assert len(resp.json["workspaces"]) == 1
    assert resp.json["preferred_workspace"] == 1
    assert len(resp.json["invitations"]) == 0
    # make sure there is no private information
    assert "passwd" not in resp.json


# login tests: success, success with email login, invalid password, missing password, not admin user
test_admin_login_data = [
    ({"login": "mergin", "password": "ilovemergin"}, 200),
    ({"login": "mergin@mergin.com", "password": "ilovemergin"}, 200),
    ({"login": "mergin", "password": "ilovemergi"}, 401),
    ({"login": "mergin"}, 400),
    ({"login": "user", "password": "user"}, 403),
]


@pytest.mark.parametrize("data,expected", test_admin_login_data)
def test_admin_login(client, data, expected):
    add_user("user", "user")
    resp = client.post("/app/admin/login", data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected


def test_update_project_v2(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    data = {"name": "new_project_name"}
    resp = client.patch(f"v2/projects/{project.id}", json=data)
    assert resp.status_code == 401
    user = add_user("test", "test")
    login(client, "test", "test")
    resp = client.patch(f"v2/projects/{project.id}", json=data)
    assert resp.status_code == 403
    login_as_admin(client)
    resp = client.patch(f"v2/projects/{project.id}", json=data)
    assert resp.status_code == 204


@patch("mergin.celery.send_email_async.apply_async")
def test_add_user(send_email_mock, client):
    """Test adding new user via public endpoint"""
    login_as_admin(client)
    data = {
        "username": "test_user",
        "email": "test@test.com",
        "password": "#pwd1234",
        "role": "reader",
        "workspace_id": test_workspace_id,
    }
    response = client.post("/v2/users", json=data)
    assert response.status_code == 201
    assert response.json["username"] == "test_user"
    assert response.json["email"] == "test@test.com"
    assert response.json["receive_notifications"] is False
    assert not send_email_mock.called

    # drop required attribute
    data.pop("email")
    assert client.post("/v2/users", json=data).status_code == 400

    # try register with the same account again
    data["email"] = "test@test.com"
    assert client.post("/v2/users", json=data).status_code == 400

    # register with optional flag sent but username missing
    data["email"] = "test2@test.com"
    data.pop("username")
    data["notify_user"] = True
    response = client.post("/v2/users", json=data)
    assert response.status_code == 201
    assert response.json["receive_notifications"] is True
    assert response.json["username"] == "test2"  # autogenerated from email
    assert send_email_mock.called
    assert send_email_mock.call_args.args[1]["subject"] == "Invitation to Mergin Maps"

    # ordinary user cannot add others
    login(client, "test2", "#pwd1234")
    assert client.post("/v2/users", json=data).status_code == 403


def test_username_generation(client):
    """Test generation of username from email"""
    assert User.generate_username("tralala@example.com") == "tralala"
    assert User.generate_username("TraLala@example.com") == "tralala"
    assert User.generate_username("tralala") is None

    # add user to test autoincrement
    user = add_user("user", "user")
    assert User.generate_username(user.email) == user.username + "1"

    user = add_user("user25", "user")
    assert User.generate_username(user.email) == user.username + "1"

    # generate username from email containing invalid chars for username, e.g. +
    assert User.generate_username("tralala+test@example.com") == "tralalatest"

    # generate username from short email
    user = add_user("t000", "user")
    assert User.generate_username("t@example.com") == "t0001"
    assert User.generate_username("t11@example.com") == "t110"

    user = add_user("support1", "user")
    assert User.generate_username("support@example.com") == "support0"

    # test long emails
    username = "a" * 25
    assert User.generate_username(f"{username}@example.com") == username
    # shortened version
    username = "a" * 50
    assert User.generate_username(f"{username}@example.com") == username[:47]

    # test username generation with existing user, case insensitive
    user = add_user("Testuser")
    assert User.generate_username("Testuser@example.com") == "testuser1"
    assert User.generate_username("testuser@example.com") == "testuser1"
    user = add_user("testuser1")
    assert User.generate_username("Testuser@example.com") == "testuser2"

    # test username with crazy long int suffix
    user = add_user("testuser13120931904")
    assert User.generate_username("Testuser@example.com") == "testuser13120931905"


def test_server_usage(client):
    """Test server usage endpoint"""
    login_as_admin(client)
    workspace = create_workspace()
    init_project = Project.query.filter_by(workspace_id=workspace.id).first()
    user = add_user()
    admin = User.query.filter_by(username="mergin").first()
    # create new project
    project = create_project("project", workspace, admin)
    project.set_role(user.id, ProjectRole.READER)
    db.session.commit()
    upload_file_to_project(project, "test.txt", client)
    resp = client.get("/app/admin/usage")
    assert resp.status_code == 200
    assert resp.json["users"] == 2
    assert resp.json["workspaces"] == 1
    assert resp.json["projects"] == 2
    assert resp.json["storage"] == project.disk_usage + init_project.disk_usage
    assert resp.json["active_monthly_contributors"] == 1
    assert resp.json["editors"] == 1
    project.set_role(user.id, ProjectRole.EDITOR)
    db.session.commit()
    resp = client.get("/app/admin/usage")
    assert resp.json["editors"] == 2
    user.inactivate()
    user.anonymize()
    project.delete()
    resp = client.get("/app/admin/usage")
    assert resp.json["editors"] == 1
    assert resp.json["users"] == 1
    assert resp.json["projects"] == 1


user_data = [
    ("user1", True),  # no problem
    ("日人日本人", True),  # non-ascii character
    ("usér", True),  # non-ascii character
    ("user\\", False),  # disallowed character
    ("user\260", True),  # non-ascii character (°)
    ("user|", False),  # vertical bar
    ("us er", False),  # space in the middle
    ("us,er", False),  # comma
    ("us—er", False),  # dash
    ("us'er", False),  # apostrophe
    (" user", True),  # starting with space (will be stripped)
    ("us.er", True),  # dot in the middle
    (".user", False),  # starting with dot
]


@pytest.mark.parametrize("username,is_valid", user_data)
def test_email_format_validation(app, username, is_valid):
    """Test email form format validation"""
    email = username + "@email.com"
    with app.test_request_context(method="POST"):
        form = ResetPasswordForm(
            data={"email": email}
        )  # ResetPasswordForm has only email field
        assert form.validate() == is_valid


def test_login_without_password(client):
    """Test password check as SSO user which does not have password"""
    login_as_admin(client)
    username = "sso_user"
    user = add_user(username=username, password="")
    user.passwd = None
    db.session.commit()
    assert user.username == username
    for pwd in ["Il0vemergin", ""]:
        resp = client.post(
            url_for("/.mergin_auth_controller_login"),
            data=json.dumps({"login": username, "password": pwd}),
            headers=json_headers,
        )
        assert resp.status_code == 401
