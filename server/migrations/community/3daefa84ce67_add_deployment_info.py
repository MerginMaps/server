# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Add deployment info table

Revision ID: 3daefa84ce67
Revises: 1fcbea2a0f2c
Create Date: 2022-12-20 15:38:57.825712

"""
import os
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3daefa84ce67"
down_revision = "1fcbea2a0f2c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mergin_info",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_reported", sa.DateTime()),
        sa.PrimaryKeyConstraint("service_id", name=op.f("pk_mergin_info")),
    )

    key = (
        uuid.UUID(os.getenv("SERVICE_ID")) if os.getenv("SERVICE_ID") else uuid.uuid4()
    )
    conn = op.get_bind()
    conn.execute(f"INSERT INTO mergin_info VALUES ('{key}')")


def downgrade():
    op.drop_table("mergin_info")
