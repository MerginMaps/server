# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import gevent
import psycogreen.gevent
import pytest
import sqlalchemy
from unittest.mock import patch

from ..app import create_simple_app, GeventTimeoutMiddleware, db
from ..config import Configuration


@pytest.mark.parametrize("use_middleware", [True, False])
def test_use_middleware(use_middleware):
    """Test using middleware"""
    with patch.object(
        Configuration,
        "GEVENT_WORKER",
        use_middleware,
    ), patch.object(
        Configuration,
        "GEVENT_REQUEST_TIMEOUT",
        1,
    ):
        application = create_simple_app()

        def ping():
            gevent.sleep(Configuration.GEVENT_REQUEST_TIMEOUT + 1)
            return "pong"

        application.add_url_rule("/test", "ping", ping)
        app_context = application.app_context()
        app_context.push()

        assert (
            isinstance(application.wsgi_app, GeventTimeoutMiddleware) == use_middleware
        )
        # in case of gevent, dummy endpoint it set to time out
        assert application.test_client().get("/test").status_code == (
            504 if use_middleware else 200
        )


def test_catch_timeout():
    """Test proper handling of gevent timeout with db.session.rollback"""
    psycogreen.gevent.patch_psycopg()
    with patch.object(
        Configuration,
        "GEVENT_WORKER",
        True,
    ), patch.object(
        Configuration,
        "GEVENT_REQUEST_TIMEOUT",
        1,
    ):
        application = create_simple_app()

        def unhandled():
            try:
                db.session.execute(sqlalchemy.text("SELECT pg_sleep(1.1);"))
            finally:
                db.session.execute(sqlalchemy.text("SELECT 1;"))
            return ""

        def timeout():
            try:
                db.session.execute(sqlalchemy.text("SELECT pg_sleep(1.1);"))
            except gevent.timeout.Timeout:
                db.session.rollback()
                raise
            finally:
                db.session.execute(sqlalchemy.text("SELECT 1;"))
            return ""

        application.add_url_rule("/unhandled", "unhandled", unhandled)
        application.add_url_rule("/timeout", "timeout", timeout)
        app_context = application.app_context()
        app_context.push()

        assert application.test_client().get("/timeout").status_code == 504

        # in case of missing rollback sqlalchemy would raise error
        with pytest.raises(sqlalchemy.exc.PendingRollbackError):
            application.test_client().get("/unhandled")

        db.session.rollback()
