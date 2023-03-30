# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Linking projects with workspaces

Revision ID: 0ab6a1fbf974
Revises: dbd428cda965
Create Date: 2022-09-01 21:38:41.949699

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0ab6a1fbf974"
down_revision = "dbd428cda965"
branch_labels = None
depends_on = None


def upgrade():
    # split project and namespace bound
    op.drop_constraint("fk_project_namespace_namespace", "project", type_="foreignkey")
    op.drop_constraint(
        "fk_project_transfer_to_ns_name_namespace",
        "project_transfer",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("uq_project_name"), "project", type_="unique")

    # add columns to relate with workspace_id
    op.add_column("project", sa.Column("workspace_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        op.f("uq_project_name"), "project", ["name", "workspace_id"]
    )
    op.create_index(
        op.f("ix_project_workspace_id"), "project", ["workspace_id"], unique=False
    )

    op.add_column(
        "removed_project", sa.Column("workspace_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_removed_project_workspace_id"),
        "removed_project",
        ["workspace_id"],
        unique=False,
    )


def downgrade():
    # revert constraints
    op.drop_constraint(op.f("uq_project_name"), "project", type_="unique")
    op.create_foreign_key(
        "fk_project_namespace_namespace",
        "project",
        "namespace",
        ["namespace"],
        ["name"],
    )
    op.create_foreign_key(
        "fk_project_transfer_to_ns_name_namespace",
        "project_transfer",
        "namespace",
        ["to_ns_name"],
        ["name"],
    )
    op.create_unique_constraint("uq_project_name", "project", ["name", "namespace"])

    # drop columns
    op.drop_index(op.f("ix_removed_project_workspace_id"), table_name="removed_project")
    op.drop_column("removed_project", "workspace_id")
    op.drop_index(op.f("ix_project_workspace_id"), table_name="project")
    op.drop_column("project", "workspace_id")
