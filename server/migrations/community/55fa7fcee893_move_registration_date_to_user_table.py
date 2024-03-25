# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
"""move registration date to user table

Revision ID: 55fa7fcee893
Revises: 8c785127e4c3
Create Date: 2024-02-21 09:38:15.685386

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "55fa7fcee893"
down_revision = "8c785127e4c3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("registration_date", sa.DateTime(), nullable=True))
    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE public."user" u
            SET registration_date = up.registration_date
            FROM public.user_profile up
            WHERE u.id = up.user_id
            """
        )
    )
    op.alter_column("user", "registration_date", nullable=False)
    op.drop_column("user_profile", "registration_date")


def downgrade():
    op.add_column(
        "user_profile",
        sa.Column(
            "registration_date",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE public.user_profile up
            SET registration_date = u.registration_date
            FROM public."user" u
            WHERE u.id = up.user_id
            """
        )
    )
    op.alter_column("user_profile", "registration_date", nullable=False)
    op.drop_column("user", "registration_date")
