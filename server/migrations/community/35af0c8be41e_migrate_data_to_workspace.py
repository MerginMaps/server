# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Migrate data from namespaces to global workspace.
Only new values are set but namespace related columns are left intact (removed in another migration script) .

Revision ID: 35af0c8be41e
Revises: 0ab6a1fbf974
Create Date: 2022-09-01 21:38:41.949699

"""
import os
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "35af0c8be41e"
down_revision = "0ab6a1fbf974"
branch_labels = None
depends_on = None

global_workspace = os.getenv("GLOBAL_WORKSPACE", None)


def upgrade():
    data_upgrade()
    op.alter_column("project", "workspace_id", nullable=False)
    op.alter_column("removed_project", "workspace_id", nullable=False)


def downgrade():
    op.alter_column("project", "workspace_id", nullable=True)
    op.alter_column("removed_project", "workspace_id", nullable=True)
    data_downgrade()


def data_upgrade():
    """Upgrade data to migrate from namespaces to global workspace:
    - projects are 'transferred' to global workspace via association with workspace id
    - projects are renamed to contain their original namespace
    - organisation-wide permissions are applied on project level
    """
    if not global_workspace:
        print("No target workspace specified - nothing to do")
        return

    conn = op.get_bind()
    # update project name to "namespace_project_name" to maintain project name unique constraint
    conn.execute(
        text(
            f"UPDATE project SET name = namespace || '_' || name WHERE namespace != '{global_workspace}'"
        )
    )
    conn.execute(
        text(
            f"UPDATE removed_project SET name = namespace || '_' || name WHERE namespace != '{global_workspace}'"
        )
    )
    # associate project with workspace ID
    conn.execute(text("UPDATE project SET workspace_id = 1"))
    conn.execute(text("UPDATE removed_project SET workspace_id = 1"))
    # transfer permissions from org to project level
    conn.execute(
        text(
            """
                WITH
                org_projects AS (
                    SELECT
                        p.id AS project_id,
                        (SELECT pa.readers || org.readers) AS new_readers,
                        (SELECT pa.writers || org.writers) AS new_writers,
                        (SELECT pa.owners || org.owners) AS new_owners
                    FROM project p
                    JOIN project_access pa ON p.id = pa.project_id
                    JOIN namespace ns ON p.namespace = ns.name
                    JOIN account a ON a.id = ns.account_id
                    JOIN organisation org ON a.owner_id = org.id
                    WHERE a.type = 'organisation' AND  pa.owners <> '{}'
                )
                UPDATE project_access
                SET
                    readers = ARRAY(SELECT DISTINCT * FROM unnest(org_projects.new_readers)),
                    writers = ARRAY(SELECT DISTINCT * FROM unnest(org_projects.new_writers)),
                    owners = ARRAY(SELECT DISTINCT * FROM unnest(org_projects.new_owners))
                FROM org_projects
                WHERE project_access.project_id = org_projects.project_id
                """
        )
    )


def data_downgrade():
    """Downgrade data from global workspace to namespaces:
    - association with workspace is removed
    - projects are renamed to drop original namespace in their name
    - project permissions are reset to default as information was reduced during data upgrade (irreversible change)
    """
    if not global_workspace:
        print("No target workspace specified - nothing to do")
        return

    conn = op.get_bind()
    conn.execute(
        text(
            f"""
            UPDATE project
            SET name = (SELECT replace(name, concat(namespace, '_'), ''))
            WHERE namespace != '{global_workspace}'
        """
        )
    )
    conn.execute(
        text(
            f"""
                UPDATE removed_project
                SET name = (SELECT replace(name, concat(namespace, '_'), ''))
                WHERE namespace != '{global_workspace}'
            """
        )
    )
    conn.execute(text("UPDATE project SET workspace_id = NULL"))
    conn.execute(text("UPDATE removed_project SET workspace_id = NULL"))
    # reset permissions to defaults
    conn.execute(
        text(
            """
            WITH
            org_projects AS (
                SELECT
                    p.id AS project_id,
                    p.creator_id AS creator_id,
                    (SELECT pa.readers || org.readers) AS new_readers,
                    (SELECT pa.writers || org.writers) AS new_writers,
                    (SELECT pa.owners || org.owners) AS new_owners
                FROM project p
                JOIN project_access pa ON p.id = pa.project_id
                JOIN namespace ns ON p.namespace = ns.name
                JOIN account a ON a.id = ns.account_id
                JOIN organisation org ON a.owner_id = org.id
                WHERE a.type = 'organisation' AND  pa.owners <> '{}'
            )

            UPDATE project_access
            SET
                readers = ARRAY(SELECT org_projects.creator_id),
                writers = ARRAY(SELECT org_projects.creator_id),
                owners = ARRAY(SELECT org_projects.creator_id)
            FROM org_projects
            WHERE project_access.project_id = org_projects.project_id
            """
        )
    )
