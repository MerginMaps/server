# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
from unittest.mock import patch
import requests

from ..app import db
from ..stats.tasks import send_statistics
from ..stats.models import MerginInfo
from .utils import Response


def test_send_statistics(app, caplog):
    """Test job to send usage statistics.
    Test opt-out, repeated request and 3rd party service errors.
    """
    info = MerginInfo.query.first()
    assert str(info.service_id) == app.config["SERVICE_ID"]
    assert not info.last_reported

    with patch("requests.post") as mock:
        mock.return_value = Response(True, {})
        app.config["COLLECT_STATISTICS"] = False
        task = send_statistics.s().apply()
        # nothing was done
        assert task.status == "SUCCESS"
        assert not info.last_reported

        # success
        app.config["COLLECT_STATISTICS"] = True
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        ts = info.last_reported
        assert ts
        url, data = mock.call_args
        assert url[0] is not None
        data = json.loads(data["data"])
        assert set(data.keys()) == {
            "licence",
            "service_uuid",
            "url",
            "projects_count",
            "users_count",
            "workspaces_count",
            "last_change",
            "server_version",
        }
        assert data["workspaces_count"] == 1
        assert data["service_uuid"] == app.config["SERVICE_ID"]
        assert data["licence"] == "ce"

        # repeated action does not do anything
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        assert info.last_reported == ts

        info.last_reported = None
        db.session.commit()
        # server responds with non-ok status
        mock.return_value = Response(False, None)
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        assert not info.last_reported
        assert "Statistics error" in caplog.text

        # server does not respond
        mock.return_value = {}
        mock.side_effect = requests.exceptions.RequestException("Some failure")
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        assert not info.last_reported
        assert "Statistics error" in caplog.text

        # pretend db was not initialized with service_id
        mock.return_value = Response(True, {})
        mock.side_effect = None
        db.session.delete(info)
        db.session.commit()
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        info = MerginInfo.query.first()
        assert info.service_id != app.config["SERVICE_ID"]
        assert info.last_reported


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
