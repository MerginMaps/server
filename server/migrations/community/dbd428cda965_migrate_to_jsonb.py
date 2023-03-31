# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Migrate project and project version json fields to jsonb

Revision ID: dbd428cda965
Revises: 836d7404f0be
Create Date: 2022-06-06 16:09:04.429156

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "dbd428cda965"
down_revision = "836d7404f0be"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        "ALTER TABLE project_version ALTER COLUMN files SET DATA TYPE jsonb USING files::jsonb;"
    )
    conn.execute(
        "ALTER TABLE project_version ALTER COLUMN changes SET DATA TYPE jsonb USING changes::jsonb;"
    )
    conn.execute(
        "ALTER TABLE project ALTER COLUMN files SET DATA TYPE jsonb USING files::jsonb;"
    )
    conn.execute(
        "CREATE INDEX ix_project_version_files_gin ON project_version USING gin (files);"
    )
    conn.execute(
        "CREATE INDEX ix_project_version_changes_gin ON project_version USING gin (changes);"
    )
    conn.execute("CREATE INDEX ix_project_files_gin ON project USING gin (files);")


def downgrade():
    conn = op.get_bind()
    conn.execute("DROP INDEX IF EXISTS ix_project_version_files_gin;")
    conn.execute("DROP INDEX IF EXISTS ix_project_version_changes_gin;")
    conn.execute("DROP INDEX IF EXISTS ix_project_files_gin;")
    conn.execute("ALTER TABLE project_version ALTER COLUMN files TYPE json;")
    conn.execute("ALTER TABLE project_version ALTER COLUMN changes TYPE json;")
    conn.execute("ALTER TABLE project ALTER COLUMN files TYPE json;")
