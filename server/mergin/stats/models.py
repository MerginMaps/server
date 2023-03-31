# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import uuid
from sqlalchemy.dialects.postgresql import UUID

from .. import db


class MerginInfo(db.Model):
    """Information about deployment"""

    service_id = db.Column(UUID(as_uuid=True), primary_key=True)
    last_reported = db.Column(db.DateTime)

    def __init__(self, service_id: str = None):
        if service_id:
            self.service_id = uuid.UUID(service_id)
        else:
            self.service_id = uuid.uuid4()
