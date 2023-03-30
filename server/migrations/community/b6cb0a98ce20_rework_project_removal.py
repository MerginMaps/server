# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Rework projects removal - drop RemovedProject, add more columns to Project table

Revision ID: b6cb0a98ce20
Revises: 3daefa84ce67
Create Date: 2023-02-21 15:46:57.825712

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b6cb0a98ce20"
down_revision = "3daefa84ce67"
branch_labels = None
depends_on = None


def upgrade():
    """Add new removed_ columns to project table and drop removed project table"""
    op.add_column("project", sa.Column("removed_at", sa.DateTime(), nullable=True))
    op.add_column("project", sa.Column("removed_by", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_project_removed_at"), "project", ["removed_at"], unique=False
    )
    op.create_index(
        op.f("ix_project_removed_by"), "project", ["removed_by"], unique=False
    )

    op.drop_table("removed_project")


def downgrade():
    """Recreate removed project table and drop removed_ columns from project table"""
    op.create_table(
        "removed_project",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("removed_by", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_removed_project")),
    )
    op.create_index(
        op.f("ix_removed_project_name"), "removed_project", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_removed_project_workspace_id"),
        "removed_project",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_removed_project_timestamp"),
        "removed_project",
        ["timestamp"],
        unique=False,
    )

    op.drop_index("ix_project_removed_at", table_name="project")
    op.drop_index("ix_project_removed_by", table_name="project")
    op.drop_column("project", "removed_at")
    op.drop_column("project", "removed_by")
