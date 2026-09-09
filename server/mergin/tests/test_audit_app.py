# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
from unittest.mock import patch

from ..app import db
from ..auth.events import AuthEventType
from ..auth.models import LoginHistory
from .utils import add_user


def test_emit_sanitizes_metadata_from_real_lockout_event(app, client, audit_capture):
    """Test event gets serialized properly"""
    user = add_user("lockme", "pass123")
    for _ in range(4):
        db.session.add(LoginHistory(user.id, "test-ua", "127.0.0.1", successful=False))
    db.session.commit()

    with patch.dict(app.config, {"LOCKOUT_POLICY": "5:300,10:3600"}):
        client.post("/app/auth/login", json={"login": "lockme", "password": "wrong"})

    e = audit_capture.one(AuthEventType.USER_UPDATED)
    json.dumps(e.metadata)

    assert e.metadata["old_locked_until"] is None
    assert isinstance(e.metadata["new_locked_until"], str)
