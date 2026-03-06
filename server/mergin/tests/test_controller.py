import os
from flask import url_for, current_app
import json
from unittest.mock import MagicMock, patch

import requests

from ..auth.models import User
from ..app import db
from .utils import Response


def test_healthcheck(client):
    # anonymous user
    client.get(url_for("/.mergin_auth_controller_logout"))
    client.application.config["WTF_CSRF_ENABLED"] = True
    maint_file = current_app.config["MAINTENANCE_FILE"]
    resp = client.post("/alive")
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    print(resp.headers)
    print(resp_data)
    assert "processing_time_ms" in resp_data
    print(type(resp_data))
    assert not resp_data["maintenance"]

    # create maintenance mode
    with open(maint_file, "w+"):
        resp = client.post("/alive")
        assert resp.status_code == 200
        resp_data = json.loads(resp.data)
        assert resp_data["maintenance"]
    os.remove(maint_file)

    # tests with invalid method
    resp = client.get("/alive")
    assert resp.status_code == 405

    # mock some db issue
    _connect = db.engine.connect
    db.engine.connect = MagicMock(side_effect=Exception("Some db issue"))
    resp = client.post("/alive")
    assert resp.status_code == 500
    # undo mock
    db.engine.connect = _connect


def test_server_updates(client):
    """Test proxy endpoint to fetch server updates information"""
    assert client.application.config["SERVER_TYPE"] == "ce"
    url = "/v1/latest-version"

    with patch("requests.get") as mock:
        api_data = {
            "ee": {"version": "2023.1.2", "info_url": "https://release-info.com"},
            "ce": {"version": "2023.1.2", "info_url": "https://release-info.com"},
        }
        mock.return_value = Response(True, api_data)
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.json["version"] == api_data["ce"]["version"]
        assert resp.json["major"] == 2023
        assert resp.json["minor"] == 1
        assert resp.json["fix"] == 2

        # remove fix version
        api_data["ce"]["version"] = "2023.2"
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.json["major"] == 2023
        assert resp.json["minor"] == 2
        assert resp.json["fix"] is None

        # invalid response
        del api_data["ce"]["version"]
        resp = client.get(url)
        assert resp.status_code == 400

        # 3rd party api failure
        mock.side_effect = requests.exceptions.RequestException("Some failure")
        resp = client.get(url)
        assert resp.status_code == 400


def test_save_diagnostic_log(client, app):
    """Test save diagnostic log endpoint"""
    user = User.query.filter(User.username == "mergin").first()
    url = url_for("/.mergin_controller_save_diagnostic_log")
    resp = client.post(url)
    assert resp.status_code == 400

    # bad request
    resp = client.post(url, data="test")
    assert resp.status_code == 400

    url = url_for("/.mergin_controller_save_diagnostic_log", app="test_app")

    # too large request
    max_size = app.config["DIAGNOSTIC_LOGS_MAX_SIZE"]
    resp = client.post(url, data="x" * (max_size + 1))
    assert resp.status_code == 413

    # invalid mime type
    resp = client.post(url, data="#!/usr/bin/python\n")
    assert resp.status_code == 400

    # valid request
    resp = client.post(url, data="test")
    assert resp.status_code == 200

    # check if file was created
    log_dir = app.config["DIAGNOSTIC_LOGS_DIR"]
    assert os.path.exists(log_dir)
    files = os.listdir(log_dir)
    assert len(files) == 1
    assert files[0].startswith(f"{user.username}_test_app_")
    assert files[0].endswith(".log")
    with open(os.path.join(log_dir, files[0]), "r") as f:
        content = f.read()
        assert content == "test"
    os.remove(os.path.join(log_dir, files[0]))

    # anonymous user
    client.get(url_for("/.mergin_auth_controller_logout"))
    # valid request
    resp = client.post(url, data="test")
    assert resp.status_code == 200
    files = os.listdir(log_dir)
    assert len(files) == 1
    assert files[0].startswith(f"anonymous_test_app_")
    assert files[0].endswith(".log")
