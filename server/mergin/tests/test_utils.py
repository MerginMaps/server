# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import base64
import json
import os
import pytest
from flask import url_for, current_app
from sqlalchemy import desc
from unittest.mock import MagicMock

from .. import db
from ..sync.utils import parse_gpkgb_header_size, gpkg_wkb_to_wkt, is_name_allowed
from ..auth.models import LoginHistory
from . import json_headers
from .utils import login


@pytest.fixture(scope="function")
def client(app):
    client = app.test_client()
    return client


def test_maintenance_mode(client):
    main_file = current_app.config["MAINTENANCE_FILE"]
    try:
        # create maintenance file
        file = open(main_file, "w+")
        login(client, "mergin", "ilovemergin")

        login_history = (
            LoginHistory.query.filter_by(username="mergin")
            .order_by(desc(LoginHistory.timestamp))
            .first()
        )
        # no login history was created because server is in maintenance mode
        assert not login_history

        resp = client.post(
            "/v1/project/{}".format("mergin"),
            data=json.dumps({"name": " foo "}),
            headers=json_headers,
        )
        assert resp.status_code == 503

        resp = client.get(url_for("/.mergin_auth_controller_logout"))
        assert resp.status_code == 200

        # delete maintenance file
        os.remove(main_file)

        login(client, "mergin", "ilovemergin")
        login_history = (
            LoginHistory.query.filter_by(username="mergin")
            .order_by(desc(LoginHistory.timestamp))
            .first()
        )
        assert login_history

        resp = client.post(
            "/v1/project/{}".format("mergin"),
            data=json.dumps({"name": " foo "}),
            headers=json_headers,
        )
        assert resp.status_code == 200
    finally:
        # delete maintenance file if tests failed
        if os.path.isfile(main_file):
            os.remove(main_file)


def test_parse_gpkg():
    # Point
    gpkg_wkb = base64.b64decode(
        "R1AAAeYQAAABAQAAAID8bic0LLE/RlTr7Iuo1j8=", validate=True
    )
    header_len = parse_gpkgb_header_size(gpkg_wkb)
    assert header_len == 8
    wkt = gpkg_wkb_to_wkt(gpkg_wkb)
    assert "POINT" in wkt

    # Linestring
    gpkg_wkb = base64.b64decode(
        "R1AAA+YQAABA0VaD5wjkv+R3O6FhidC/hn8DkdjL0z8Iwc3FqhvlPwECAAAABAAAAGhDvPBvINK/CMHNxaob5T9I139WMEjZv+DthIYlQuA/5Hc7oWGJ0L+GfwOR2MvTP0DRVoPnCOS/zB9sPJo/2D8=",
        validate=True,
    )
    header_len = parse_gpkgb_header_size(gpkg_wkb)
    assert header_len == 40
    wkt = gpkg_wkb_to_wkt(gpkg_wkb)
    assert "LINESTRING" in wkt

    # Invalid
    gpkg_wkb = base64.b64decode("aaaa", validate=True)
    header_len = parse_gpkgb_header_size(gpkg_wkb)
    assert header_len == -1
    wkt = gpkg_wkb_to_wkt(gpkg_wkb)
    assert not wkt


def test_healthcheck(client):
    client.application.config["WTF_CSRF_ENABLED"] = True
    maint_file = current_app.config["MAINTENANCE_FILE"]
    resp = client.post("/alive")
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert "processing_time_ms" in resp_data
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


def test_is_name_allowed():
    test_cases = [
        ("project", True),
        ("ProJect", True),
        ("Pro123ject", True),
        ("123PROJECT", True),
        ("PROJECT", True),
        ("project ", True),
        ("pro ject", True),
        ("proj-ect", True),
        ("-project", True),
        ("proj_ect", True),
        ("proj.ect", True),
        ("proj!ect", True),
        (" project", False),
        (".project", False),
        ("proj~ect", False),
        ("pro\ject", False),
        ("pro/ject", False),
        ("pro|ject", False),
        ("pro+ject", False),
        ("pro=ject", False),
        ("pro>ject", False),
        ("pro<ject", False),
        ("pro@ject", False),
        ("pro#ject", False),
        ("pro$ject", False),
        ("pro%ject", False),
        ("pro^ject", False),
        ("pro&ject", False),
        ("pro*ject", False),
        ("pro?ject", False),
        ("pro:ject", False),
        ("pro;ject", False),
        ("pro,ject", False),
        ("pro`ject", False),
        ("pro'ject", False),
        ('pro"ject', False),
        ("projectz", True),
        ("projectZ", True),
        ("project0", True),
        ("pro(ject", False),
        ("pro)ject", False),
        ("pro{ject", False),
        ("pro}ject", False),
        ("pro[ject", False),
        ("pro]ject", False),
        ("pro]ject", False),
        ("CON", False),
        ("NUL", False),
        ("NULL", True),
        ("PRN", False),
        ("LPT0", False),
        ("lpt0", True),
        ("LPT1", False),
        ("lpt1", True),
        ("COM1", False),
        ("com1", True),
        ("AUX", False),
        ("AuX", True),
        ("projAUXect", True),
        ("CONproject", True),
        ("projectCON", True),
        ("support", False),
        ("helpdesk", False),
        ("input", False),
        ("lutraconsulting", False),
        ("lutra", False),
        ("merginmaps", False),
        ("mergin", False),
        ("admin", False),
        ("sales", False),
        ("", False),
        ("    ", False),
    ]

    for t in test_cases:
        assert is_name_allowed(t[0]) == t[1]
