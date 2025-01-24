# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from dataclasses import dataclass
from typing import Optional
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

from ..app import db


@dataclass
class ServerCallhomeData:
    service_uuid: Optional[str]
    url: Optional[str]
    contact_email: Optional[str]
    licence: Optional[str]
    projects_count: Optional[int]
    users_count: Optional[int]
    workspaces_count: Optional[int]
    last_change: Optional[str]
    server_version: Optional[str]
    monthly_contributors: Optional[int]
    editors: Optional[int]


class MerginInfo(db.Model):
    """Information about deployment"""

    service_id = db.Column(UUID(as_uuid=True), primary_key=True)
    last_reported = db.Column(db.DateTime)

    def __init__(self, service_id: str = None):
        if service_id:
            self.service_id = uuid.UUID(service_id)
        else:
            self.service_id = uuid.uuid4()


class MerginStatistics(db.Model):
    """Information about deployment"""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(
        db.DateTime, index=True, nullable=False, server_default="now()"
    )
    # data with statistics
    data = db.Column(db.JSON)
