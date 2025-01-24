# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import csv
from dataclasses import asdict
from datetime import timedelta, timezone, datetime
import json
from unittest.mock import patch
import requests
from sqlalchemy.sql.operators import is_

from mergin.auth.models import User
from mergin.sync.models import Project, ProjectRole

from ..app import db
from ..stats.tasks import get_callhome_data, save_statistics, send_statistics
from ..stats.models import MerginInfo, MerginStatistics, ServerCallhomeData
from .utils import Response, add_user, create_project, create_workspace


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
        app.config["CONTACT_EMAIL"] = "test@example.com"
        user = add_user()
        admin = User.query.filter_by(username="mergin").first()
        # create new project
        workspace = create_workspace()
        project = create_project("project", workspace, admin)
        project.set_role(user.id, ProjectRole.EDITOR)
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
            "contact_email",
            "projects_count",
            "users_count",
            "workspaces_count",
            "last_change",
            "server_version",
            "monthly_contributors",
            "editors",
        }
        assert data["workspaces_count"] == 1
        assert data["service_uuid"] == app.config["SERVICE_ID"]
        assert data["licence"] == "ce"
        assert data["monthly_contributors"] == 1
        assert data["users_count"] == 2
        assert data["projects_count"] == 2
        assert data["contact_email"] == "test@example.com"
        assert data["editors"] == 2

        # repeated action does not do anything
        task = send_statistics.s().apply()
        assert task.status == "SUCCESS"
        assert info.last_reported == ts

        # project removed / users removed in time
        info.last_reported = None
        project.delete()
        user.inactivate()
        user.anonymize()
        db.session.commit()
        task = send_statistics.s().apply()
        url, data = mock.call_args
        data = json.loads(data["data"])
        assert data["projects_count"] == 1
        assert data["users_count"] == 1
        assert data["editors"] == 1

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


def test_save_statistics(app, client):
    """Test save statistics celery job"""
    info = MerginInfo.query.first()
    app.config["CONTACT_EMAIL"] = "test@example.com"
    assert MerginStatistics.query.count() == 0
    save_statistics.s().apply()
    assert MerginStatistics.query.count() == 1
    stats = MerginStatistics.query.order_by(MerginStatistics.created_at.desc()).first()
    stats_json_data = get_callhome_data(info)
    assert stats.created_at
    assert stats.data == asdict(stats_json_data)

    # debouncing
    save_statistics.s().apply()
    assert MerginStatistics.query.count() == 1
    stats.created_at = datetime.now(timezone.utc) - timedelta(hours=12)
    save_statistics.s().apply()
    assert MerginStatistics.query.count() == 2


def test_download_report(app, client):
    """Test download report endpoint"""
    url = "/app/admin/report"
    resp = client.get(url)
    resp.status_code == 400

    # bad date format
    resp = client.get(f"{url}?date_from=2021-01-01T00:00:00&date_to=2021-01-01")
    assert resp.status_code == 400

    app.config["CONTACT_EMAIL"] = "test@example.com"
    save_statistics.s().apply()
    resp = client.get(
        f"{url}?date_from=2021-01-01&date_to={datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    lines = resp.data.splitlines()
    assert len(lines) == 2

    stat = MerginStatistics.query.first()
    keys = list(asdict(ServerCallhomeData(**stat.data)).keys()) + ["created_at"]
    assert lines[0].decode("UTF-8") == ",".join(keys)

    # test same day
    stat.created_at = datetime(2021, 1, 1, tzinfo=timezone.utc)
    db.session.commit()

    resp = client.get(
        f"{url}?date_from=2021-01-01&date_to={datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    lines = resp.data.splitlines()
    assert len(lines) == 2

    # empty response
    stat.created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.session.commit()
    resp = client.get(
        f"{url}?date_from=2021-01-01&date_to={datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    lines = resp.data.splitlines()
    empty_file = f"{','.join(keys)}\r\n"
    assert resp.data.decode("UTF-8") == empty_file
    assert len(lines) == 1
