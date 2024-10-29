# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import gevent
import pytest

from ..app import create_simple_app, GeventTimeoutMiddleware
from ..config import Configuration


@pytest.mark.parametrize("use_middleware", [True, False])
def test_use_middleware(use_middleware):
    """Test using middleware"""
    Configuration.GEVENT_WORKER = use_middleware
    Configuration.GEVENT_REQUEST_TIMEOUT = 1
    application = create_simple_app()

    def ping():
        gevent.sleep(Configuration.GEVENT_REQUEST_TIMEOUT + 1)
        return "pong"

    application.add_url_rule("/test", "ping", ping)
    app_context = application.app_context()
    app_context.push()

    assert isinstance(application.wsgi_app, GeventTimeoutMiddleware) == use_middleware
    # in case of gevent, dummy endpoint it set to time out
    assert (
        application.test_client().get("/test").status_code == 502
        if use_middleware
        else 200
    )
