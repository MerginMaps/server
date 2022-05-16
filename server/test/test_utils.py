# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import json
import os
import pytest
from flask import url_for, current_app
from sqlalchemy import desc

from src.auth.models import LoginHistory
from . import json_headers
from .utils import login


@pytest.fixture(scope='function')
def client(app):
    client = app.test_client()
    return client


def test_maintenance_mode(client):
    main_file = current_app.config['MAINTENANCE_FILE']
    try:
        # create maintenance file
        file = open(main_file, 'w+')
        login(client, "mergin", "ilovemergin")

        login_history = LoginHistory.query.filter_by(username='mergin').order_by(
            desc(LoginHistory.timestamp)).first()
        # no login history was created because server is in maintenance mode
        assert not login_history

        resp = client.post('/v1/project/{}'.format('mergin'), data=json.dumps({"name": ' foo '}), headers=json_headers)
        assert resp.status_code == 503

        resp = client.get(url_for('auth.logout'))
        assert resp.status_code == 200

        # delete maintenance file
        os.remove(main_file)

        login(client, "mergin", "ilovemergin")
        login_history = LoginHistory.query.filter_by(username='mergin').order_by(
            desc(LoginHistory.timestamp)).first()
        assert login_history

        resp = client.post('/v1/project/{}'.format('mergin'), data=json.dumps({"name": ' foo '}), headers=json_headers)
        assert resp.status_code == 200
    finally:
        # delete maintenance file if test failed
        if os.path.isfile(main_file):
            os.remove(main_file)

