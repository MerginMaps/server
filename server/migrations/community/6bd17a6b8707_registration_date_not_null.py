# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Add Not NULL constraint to registration_date

Revision ID: 6bd17a6b8707
Revises: 3a77058a2fd7
Create Date: 2024-02-13 13:54:37.632996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6bd17a6b8707"
down_revision = "3a77058a2fd7"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # assign some random value to user_profile registration_date field if empty
    conn.execute(
        sa.text(
            """
    update user_profile
    set registration_date = '2000-01-01 10:00:00.0'
    where registration_date is Null
    """
        )
    )

    op.alter_column("user_profile", "registration_date", nullable=False)


def downgrade():
    op.alter_column("user_profile", "registration_date", nullable=True)
