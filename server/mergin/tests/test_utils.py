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

from ..app import db
from ..sync.utils import (
    parse_gpkgb_header_size,
    gpkg_wkb_to_wkt,
    is_reserved_word,
    has_valid_characters,
    has_valid_first_character,
    check_filename,
    is_valid_path,
    get_x_accel_uri,
)
from ..auth.models import LoginHistory, User
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

        user = User.query.filter_by(username="mergin").first()
        login_history = (
            LoginHistory.query.filter_by(user_id=user.id)
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
            LoginHistory.query.filter_by(user_id=user.id)
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
        # Not valid filename
        ("project ", False),
        ("pro ject", True),
        ("proj-ect", True),
        ("-project", True),
        ("proj_ect", True),
        ("proj.ect", True),
        # We are removing ! from valids
        ("proj!ect", False),
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
        # is not reserved word
        ("LPT0", True),
        ("lpt0", True),
        ("LPT1", False),
        ("lpt1", False),
        ("COM1", False),
        ("com1", False),
        ("AUX", False),
        ("AuX", False),
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
        ("😄guy", False),
        ("会社", True),
    ]

    for t in test_cases:
        name = t[0]
        expected = t[1]
        assert (
            not (
                has_valid_characters(name)
                and has_valid_first_character(name)
                and check_filename(name)
                and is_reserved_word(name)
            )
            == expected
        )


filepaths = [
    ("/home/user/mm/project/survey.gpkg", False),
    ("C:\Documents\Summer2018.pdf", False),
    ("\Desktop\Summer2019.pdf", False),
    ("../image.png", False),
    ("./image.png", False),
    ("assets/photos/im?age.png", False),
    ("assets/photos/CON.png", False),
    ("assets/photos/CONfile.png", True),
    ("image.png", True),
    ("images/image.png", True),
    ("media/photos/image.png", True),
    ("med..ia/pho.tos/ima...ge.png", True),
    ("med/../ia/pho.tos/ima...ge.png", False),
]


@pytest.mark.parametrize("filepath,allow", filepaths)
def test_is_valid_path(client, filepath, allow):
    assert is_valid_path(filepath) == allow


def test_get_x_accell_uri(client):
    """Test get_x_accell_uri"""
    client.application.config["LOCAL_PROJECTS"] = "/data/"
    # Input URL parts
    url_parts = ("/data", "archive", "project1", "file.txt")
    # Expected result
    expected = "/download/archive/project1/file.txt"
    assert get_x_accel_uri(*url_parts) == expected

    url_parts = ("archive", "project1", "file.txt")
    assert get_x_accel_uri(*url_parts) == expected

    url_parts = ()
    assert get_x_accel_uri(*url_parts) == "/download"

    url_parts = ("/archive", "cc900b78-a8b2-4e80-b546-74c96584bd10-v4.zip")
    assert (
        get_x_accel_uri(*url_parts)
        == "/download/archive/cc900b78-a8b2-4e80-b546-74c96584bd10-v4.zip"
    )
