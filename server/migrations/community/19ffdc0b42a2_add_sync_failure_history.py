# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Add sync failure history

Revision ID: 19ffdc0b42a2
Revises: 2686074eff45
Create Date: 2021-11-05 08:57:48.246406

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "19ffdc0b42a2"
down_revision = "2686074eff45"
branch_labels = ("community",)
depends_on = None


def upgrade():
    op.create_table(
        "sync_failures_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_namespace", sa.String(), nullable=True),
        sa.Column("project_name", sa.String(), nullable=True),
        sa.Column("last_version", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("error_details", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_failures_history")),
    )

    op.create_index(
        op.f("ix_sync_failures_history_error_details"),
        "sync_failures_history",
        ["error_details"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_error_type"),
        "sync_failures_history",
        ["error_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_last_version"),
        "sync_failures_history",
        ["last_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_project_id"),
        "sync_failures_history",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_project_name"),
        "sync_failures_history",
        ["project_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_project_namespace"),
        "sync_failures_history",
        ["project_namespace"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_timestamp"),
        "sync_failures_history",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sync_failures_history_user_agent"),
        "sync_failures_history",
        ["user_agent"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_sync_failures_history_user_agent"), table_name="sync_failures_history"
    )
    op.drop_index(
        op.f("ix_sync_failures_history_timestamp"), table_name="sync_failures_history"
    )
    op.drop_index(
        op.f("ix_sync_failures_history_project_namespace"),
        table_name="sync_failures_history",
    )
    op.drop_index(
        op.f("ix_sync_failures_history_project_name"),
        table_name="sync_failures_history",
    )
    op.drop_index(
        op.f("ix_sync_failures_history_project_id"), table_name="sync_failures_history"
    )
    op.drop_index(
        op.f("ix_sync_failures_history_last_version"),
        table_name="sync_failures_history",
    )
    op.drop_index(
        op.f("ix_sync_failures_history_error_type"), table_name="sync_failures_history"
    )
    op.drop_index(
        op.f("ix_sync_failures_history_error_details"),
        table_name="sync_failures_history",
    )
    op.drop_table("sync_failures_history")
