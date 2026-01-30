# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import uuid
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

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
    sso_connections: Optional[int]


class MerginInfo(db.Model):
    """Information about deployment"""

    service_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    last_reported: Mapped[Optional[datetime]]

    def __init__(self, service_id: str = None):
        if service_id:
            self.service_id = uuid.UUID(service_id)
        else:
            self.service_id = uuid.uuid4()


class MerginStatistics(db.Model):
    """Information about deployment"""

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(index=True, default=datetime.utcnow)
    # data with statistics
    data: Mapped[dict] = mapped_column(JSONB)
