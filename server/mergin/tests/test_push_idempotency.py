# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from ..app import db
from ..sync.config import Configuration
from ..sync.models import (
    FileSyncErrorType,
    Project,
    PushIdempotencyKey,
    Upload,
)
from ..sync.tasks import cleanup_push_idempotency_keys
from . import json_headers, test_project, test_project_dir, test_workspace_id
from .test_project_controller import (
    _get_changes,
    _get_changes_without_added,
    create_transaction,
    upload_chunks,
)
from .utils import file_info


def _idempotency_headers(key=None):
    """Return json_headers extended with an Mm-push-id key."""
    return {**json_headers, "Mm-push-id": key or str(uuid.uuid4())}


def test_v1_idempotency_success(client):
    """Second call with same key returns cached 200 without creating a new version."""
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)
    key = str(uuid.uuid4())

    resp1 = client.post(
        f"/v1/project/push/finish/{upload.transaction_id}",
        headers=_idempotency_headers(key),
    )
    assert resp1.status_code == 200
    assert PushIdempotencyKey.query.get(key) is not None

    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    version_after_first = project.latest_version

    # second call with to prove it is not re-executed — the cached response is returned based on the key alone
    resp2 = client.post(
        f"/v1/project/push/finish/{upload.transaction_id}",
        headers=_idempotency_headers(key),
    )
    assert resp2.status_code == 200
    assert resp2.json == resp1.json
    assert project.latest_version == version_after_first


def test_v1_idempotency_sync_error_cached(client):
    """Sync error (corrupted files) is cached; second call returns same error."""
    changes = _get_changes(test_project_dir)
    upload, _ = create_transaction("mergin", changes)
    # intentionally do NOT upload chunks — process_chunks will report corrupted files
    key = str(uuid.uuid4())

    resp1 = client.post(
        f"/v1/project/push/finish/{upload.transaction_id}",
        headers=_idempotency_headers(key),
    )
    assert resp1.status_code == 422
    assert "corrupted_files" in resp1.json["detail"]

    record = PushIdempotencyKey.query.get(key)
    assert record is not None
    assert record.response["status_code"] == 422

    # second call — returns cached error
    resp2 = client.post(
        f"/v1/project/push/finish/{upload.transaction_id}",
        headers=_idempotency_headers(key),
    )
    assert resp2.status_code == 422
    assert resp2.json == resp1.json


def test_v1_non_sync_errors_not_cached(client):
    """404 and 403 errors are not cached."""
    key = str(uuid.uuid4())

    resp = client.post(
        f"/v1/project/push/finish/{str(uuid.uuid4())}",
        headers=_idempotency_headers(key),
    )
    assert resp.status_code == 404
    assert PushIdempotencyKey.query.get(key) is None


def test_v1_no_idempotency_key(client):
    """Requests without Mm-push-id header are unaffected — no record stored."""
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)

    resp = client.post(
        f"/v1/project/push/finish/{upload.transaction_id}", headers=json_headers
    )
    assert resp.status_code == 200
    assert PushIdempotencyKey.query.count() == 0


def test_v2_idempotency_success(client):
    """Second call with same key returns cached 201 without creating a new version."""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    # use only a remove — no chunks needed, avoids "file already exists" validation error
    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "removed": [file_info(test_project_dir, "base.gpkg")],
            "updated": [],
        },
    }
    key = str(uuid.uuid4())

    resp1 = client.post(
        f"v2/projects/{project.id}/versions",
        json=data,
        headers=_idempotency_headers(key),
    )
    assert resp1.status_code == 201
    assert PushIdempotencyKey.query.get(key) is not None
    version_after_first = project.latest_version

    # second call — cached response, no new version created
    resp2 = client.post(
        f"v2/projects/{project.id}/versions",
        json=data,
        headers=_idempotency_headers(key),
    )
    assert resp2.status_code == 201
    assert resp2.json == resp1.json
    assert project.latest_version == version_after_first


def test_v2_idempotency_datasync_error_cached(client):
    """DataSyncError response is cached; second call returns the same error."""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    # no added files — avoid "file already exists" validation error
    changes = _get_changes_without_added(test_project_dir)
    data = {"version": "v1", "changes": changes}
    key = str(uuid.uuid4())

    sync_errors = {
        f["path"]: f"{FileSyncErrorType.SYNC_ERROR.value}: err"
        for f in changes["updated"]
    }
    with patch.object(Upload, "process_chunks", return_value=({}, sync_errors)):
        resp1 = client.post(
            f"v2/projects/{project.id}/versions",
            json=data,
            headers=_idempotency_headers(key),
        )
    assert resp1.status_code == 422
    assert resp1.json["code"] == "DataSyncError"
    assert resp1.headers["Content-Type"] == "application/problem+json"

    record = PushIdempotencyKey.query.get(key)
    assert record is not None
    assert record.response["content_type"] == "application/problem+json"

    resp2 = client.post(
        f"v2/projects/{project.id}/versions",
        json=data,
        headers=_idempotency_headers(key),
    )
    assert resp2.status_code == 422
    assert resp2.json == resp1.json
    assert resp2.headers["Content-Type"] == "application/problem+json"


def test_v2_non_sync_errors_not_cached(client):
    """StorageLimitHit, ProjectLocked and similar errors are not cached."""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    data = {"version": "v1", "changes": {"added": [], "updated": [], "removed": []}}
    key = str(uuid.uuid4())

    project.locked_until = datetime.utcnow() + timedelta(days=1)
    db.session.commit()

    resp = client.post(
        f"v2/projects/{project.id}/versions",
        json=data,
        headers=_idempotency_headers(key),
    )
    assert resp.status_code == 423
    assert PushIdempotencyKey.query.get(key) is None

    project.locked_until = None
    db.session.commit()


def test_v2_check_only_not_cached(client):
    """check_only dry-run responses are never cached."""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    # use a valid remove-only change so all validation passes and check_only is reached
    data = {
        "version": "v1",
        "changes": {
            "added": [],
            "removed": [file_info(test_project_dir, "base.gpkg")],
            "updated": [],
        },
        "check_only": True,
    }
    key = str(uuid.uuid4())

    resp = client.post(
        f"v2/projects/{project.id}/versions",
        json=data,
        headers=_idempotency_headers(key),
    )
    assert resp.status_code == 204
    assert PushIdempotencyKey.query.get(key) is None


def test_cleanup_push_idempotency_keys(client):
    """Cleanup task removes keys older than PUSH_IDEMPOTENCY_KEY_EXPIRATION."""
    fresh_key = str(uuid.uuid4())
    expired_key = str(uuid.uuid4())

    PushIdempotencyKey.store(fresh_key, 201, "{}", "application/json")

    # manually insert an already-expired record
    expired = PushIdempotencyKey(
        key=expired_key,
        response={"status_code": 201, "body": "{}", "content_type": "application/json"},
        created=datetime.utcnow()
        - timedelta(seconds=Configuration.PUSH_IDEMPOTENCY_KEY_EXPIRATION + 1),
    )
    db.session.add(expired)
    db.session.commit()

    assert PushIdempotencyKey.query.count() == 2

    cleanup_push_idempotency_keys()

    assert PushIdempotencyKey.query.count() == 1
    assert PushIdempotencyKey.query.get(fresh_key) is not None
    assert PushIdempotencyKey.query.get(expired_key) is None
