# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Drop namespace related objects

Revision ID: 1fcbea2a0f2c
Revises: 0ab6a1fbf974
Create Date: 2022-12-20 15:38:57.825712

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "1fcbea2a0f2c"
down_revision = "0ab6a1fbf974"
branch_labels = None
depends_on = None


def upgrade():
    """Irreversibly drop namespace related objects"""
    op.drop_table("organisation_invitation")
    op.drop_table("organisation")
    op.drop_table("project_transfer")
    op.drop_table("namespace")
    op.drop_table("account")

    op.drop_column("project", "namespace")
    op.drop_column("removed_project", "namespace")
    op.drop_column("access_request", "namespace")
    op.drop_column("sync_failures_history", "project_name")
    op.drop_column("sync_failures_history", "project_namespace")


def downgrade():
    """Drop of namespace related tables and columns is irreversible"""
    pass
