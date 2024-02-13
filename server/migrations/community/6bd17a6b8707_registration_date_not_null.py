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
    with null_registration_date as (
        select *
        from user_profile
        where registration_date is Null
        )
    update user_profile up
    set registration_date = '2000-01-01 10:00:00.0'
    from null_registration_date
    where up.user_id = null_registration_date.user_id
    """
        )
    )

    op.alter_column("user_profile", "registration_date", nullable=False)


def downgrade():
    op.alter_column("user_profile", "registration_date", nullable=True)
