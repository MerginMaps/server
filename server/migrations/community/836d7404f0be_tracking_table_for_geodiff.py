# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Add geodiff actions tracking table

Revision ID: 836d7404f0be
Revises: 19ffdc0b42a2
Create Date: 2022-01-27 09:15:25.002915

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "836d7404f0be"
down_revision = "19ffdc0b42a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "geodiff_action_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_version", sa.String(), nullable=False),
        sa.Column("target_version", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size", sa.BIGINT(), nullable=True),
        sa.Column("diff_size", sa.Integer(), nullable=True),
        sa.Column("changes", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("copy_time", sa.Float(), nullable=True),
        sa.Column("checksum_time", sa.Float(), nullable=True),
        sa.Column("geodiff_time", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_geodiff_action_history")),
    )
    op.create_index(
        op.f("ix_geodiff_action_history_action"),
        "geodiff_action_history",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geodiff_action_history_file_name"),
        "geodiff_action_history",
        ["file_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geodiff_action_history_project_id"),
        "geodiff_action_history",
        ["project_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_geodiff_action_history_project_id"),
        table_name="geodiff_action_history",
    )
    op.drop_index(
        op.f("ix_geodiff_action_history_file_name"), table_name="geodiff_action_history"
    )
    op.drop_index(
        op.f("ix_geodiff_action_history_action"), table_name="geodiff_action_history"
    )
    op.drop_table("geodiff_action_history")
