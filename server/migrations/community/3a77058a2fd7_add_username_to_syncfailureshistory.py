# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""add username to SyncFailuresHistory

Revision ID: 3a77058a2fd7
Revises: b6cb0a98ce20
Create Date: 2023-09-05 23:54:37.632996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3a77058a2fd7"
down_revision = "b6cb0a98ce20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sync_failures_history", sa.Column("user_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_sync_failures_history_user_id_user",
        "sync_failures_history",
        "user",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_sync_failures_history_user_id_user",
        "sync_failures_history",
        type_="foreignkey",
    )
    op.drop_column("sync_failures_history", "user_id")
