"""Migrate away from jsonb columns in project and project_version tables, introduce new file history table

Revision ID: c13819c566e7
Revises: 07f2185e2428
Create Date: 2024-06-06 16:05:59.565541

"""

import time
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c13819c566e7"
down_revision = "07f2185e2428"
branch_labels = None
depends_on = None


push_change_type = postgresql.ENUM(
    "create", "update", "delete", "update_diff", name="push_change_type"
)


def upgrade():
    conn = op.get_bind()
    op.create_table(
        "file_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=False),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("change", push_change_type, nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["project_version.id"],
            name=op.f("fk_file_history_version_id_project_version"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_history")),
        sa.UniqueConstraint(
            "version_id", "path", name=op.f("uq_file_history_version_id")
        ),
    )
    op.create_index(
        op.f("ix_file_history_change"), "file_history", ["change"], unique=False
    )
    op.create_index(
        op.f("ix_file_history_path"), "file_history", ["path"], unique=False
    )
    op.create_index(
        op.f("ix_file_history_version_id"), "file_history", ["version_id"], unique=False
    )

    data_upgrade()

    # optionally drop gin indices (only added by old alembic migration, not present in new databases)
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_project_files_gin;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_project_version_changes_gin;"))
    conn.execute(
        sa.text("DROP INDEX IF EXISTS ix_project_ix_project_version_files_gin;")
    )

    op.drop_column("project", "files")

    op.drop_index(op.f("ix_project_version_name"), table_name="project_version")
    op.drop_index(op.f("ix_project_latest_version"), table_name="project")
    op.drop_column("project_version", "files")
    op.drop_column("project_version", "changes")

    # harmonize constraint name
    op.drop_constraint("uq_project_id_version", "project_version", type_="unique")

    # trim 'v' prefix and convert to integer
    conn.execute(
        sa.text(
            "ALTER TABLE project_version ALTER COLUMN name SET DATA TYPE integer USING ltrim(name, 'v')::integer;"
        )
    )
    conn.execute(
        sa.text(
            "ALTER TABLE project ALTER COLUMN latest_version SET DATA TYPE integer USING ltrim(latest_version, 'v')::integer;"
        )
    )

    op.alter_column(
        "project",
        "latest_version",
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        existing_nullable=True,
    )

    op.alter_column(
        "project_version",
        "name",
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        existing_nullable=True,
    )

    op.create_index(
        op.f("ix_project_version_name"), "project_version", ["name"], unique=False
    )

    op.create_index(
        op.f("ix_project_latest_version"), "project", ["latest_version"], unique=False
    )

    op.create_unique_constraint(
        op.f("uq_project_version_project_id"), "project_version", ["project_id", "name"]
    )


def data_upgrade():
    conn = op.get_bind()
    # split json aggregate to individual file changes, rename action is split to create and delete file actions
    query = """
    WITH history AS (
        WITH all_changes AS (
            SELECT DISTINCT
                pv.id as version_id,
                pv.name,
                pv.created,
                pv.changes
            FROM project_version pv
            ORDER BY pv.created
        ), renamed_files AS (
            SELECT DISTINCT
                version_id,
                name,
                jsonb_array_elements((changes ->> 'renamed')::jsonb) AS file,
                'rename' AS change
            FROM all_changes
        ), regular_files AS (
            SELECT DISTINCT
                version_id,
                name,
                jsonb_array_elements((changes ->> 'added')::jsonb) as file,
                'create' AS change
            FROM all_changes
            UNION
            SELECT DISTINCT
                version_id,
                name,
                jsonb_array_elements((changes ->> 'updated')::jsonb) as file,
                'update' AS change
            FROM all_changes
            UNION
            SELECT DISTINCT
                version_id,
                name,
                jsonb_array_elements((changes ->> 'removed')::jsonb) as file,
                'delete' AS change
            FROM all_changes
        )
        SELECT
            version_id,
            'delete' AS change,
            file ->> 'path' AS path,
            COALESCE(file ->> 'location', name || '/' || COALESCE(file ->> 'sanitized_path', file ->> 'path')) AS location,
            (file ->> 'size')::bigint AS size,
            (file ->> 'checksum') AS checksum,
            (file ->> 'diff')::jsonb - 'mtime' - 'sanitized_path' AS diff
        FROM renamed_files
        UNION
        SELECT
            version_id,
            'create' AS change,
            file ->> 'new_path' AS path,
            COALESCE(file ->> 'location', name || '/' || COALESCE(file ->> 'sanitized_path', file ->> 'path')) AS location,
            (file ->> 'size')::bigint AS size,
            (file ->> 'checksum') AS checksum,
            (file ->> 'diff')::jsonb - 'mtime' - 'sanitized_path' AS diff
        FROM renamed_files
        UNION
        SELECT
            version_id,
            CASE
                WHEN change = 'update' AND (file ->> 'diff')::jsonb ->> 'path' IS NOT NULL THEN 'update_diff'
                ELSE change
            END AS change,
            file ->> 'path' AS path,
            COALESCE(file ->> 'location', name || '/' || COALESCE(file ->> 'sanitized_path', file ->> 'path')) AS location,
            (file ->> 'size')::bigint AS size,
            (file ->> 'checksum') AS checksum,
            (file ->> 'diff')::jsonb - 'mtime' - 'sanitized_path' AS diff
        FROM regular_files
    )
    INSERT INTO file_history (version_id, path, location, size, checksum, diff, change)
    SELECT version_id, path, location, size, checksum, diff, change::push_change_type FROM history;
    """
    conn.execute(sa.text(query))


def data_downgrade():
    conn = op.get_bind()

    first_version_files_query = """
    WITH first_pushes AS (
        SELECT
            pv.id AS version_id,
            jsonb_build_object(
                'path', fh.path,
                'size', fh.size,
                'checksum', fh.checksum,
                'location', fh.location,
                'sanitized_path', ltrim(fh.location, pv.name || '/'),
                'mtime', pv.created
            ) AS file
        FROM file_history fh
        LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
        WHERE pv.name = 1
    )
    UPDATE project_version pv
    SET files = first_pushes.files
    FROM first_pushes
    WHERE first_pushes.version_id = pv.id;
    """

    # construct version files and changes, update project files with latest version files
    version_files_query = """
    WITH version_files AS (
        WITH version_files_changes AS (
            WITH history AS (
                SELECT
                    fh.*,
                    pv.project_id,
                    pv.name
                FROM file_history fh
                LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
            )
            SELECT DISTINCT
                pv.project_id,
                pv.id AS version_id,
                FIRST_VALUE (h.id) OVER (
                    PARTITION BY (h.path, pv.id)
                    ORDER BY h.name DESC
                ) AS fh_id
            FROM project_version pv
            LEFT OUTER JOIN history h ON pv.project_id = h.project_id
            WHERE h.name <= pv.name
        )
        SELECT
            vf.version_id,
            CASE
                WHEN fh.diff IS NOT NULL THEN
                        jsonb_build_object(
                            'path', fh.path,
                            'size', fh.size,
                            'checksum', fh.checksum,
                            'diff', fh.diff || jsonb_build_object('mtime', pv.created, 'sanitized_path', ltrim(fh.diff ->> 'location', pv.name || '/')),
                            'location', fh.location,
                            'sanitized_path', ltrim(fh.location, pv.name || '/'),
                            'mtime', pv.created
                        )
                ELSE
                        jsonb_build_object(
                            'path', fh.path,
                            'size', fh.size,
                            'checksum', fh.checksum,
                            'location', fh.location,
                            'sanitized_path', ltrim(fh.location, pv.name || '/'),
                            'mtime', pv.created
                        )
            END AS file
            FROM project_version pv
            LEFT OUTER JOIN version_files_changes vf ON pv.id = vf.version_id
            LEFT OUTER JOIN file_history fh ON fh.id = vf.fh_id
            WHERE fh.change::text != 'delete'
            GROUP BY vf.version_id, fh.diff, fh.path, fh.size, fh.checksum, fh.location, pv.created, pv.name
    ), aggregates AS (
    SELECT
        version_id,
        jsonb_agg(file) AS files
    FROM version_files
    GROUP BY version_id
    )
    UPDATE project_version pv
    SET files = a.files
    FROM aggregates a
    WHERE a.version_id = pv.id;
    """

    # renamed files are reconstructed as delete-create pairs
    version_changes_query = """
    WITH changes AS NOT MATERIALIZED (
        WITH history AS NOT MATERIALIZED (
            SELECT
                pv.id AS version_id,
                CASE
                    WHEN fh.diff IS NOT NULL THEN
                        jsonb_build_object(
                            'path', fh.path,
                            'size', fh.size,
                            'checksum', fh.checksum,
                            'diff', fh.diff || jsonb_build_object('mtime', pv.created, 'sanitized_path', ltrim(fh.diff ->> 'location', pv.name || '/')),
                            'location', fh.location,
                            'sanitized_path', ltrim(fh.location, pv.name || '/'),
                            'mtime', pv.created
                        )
                    ELSE
                        jsonb_build_object(
                            'path', fh.path,
                            'size', fh.size,
                            'checksum', fh.checksum,
                            'location', fh.location,
                            'sanitized_path', ltrim(fh.location, pv.name || '/'),
                            'mtime', pv.created
                        )
                END AS file,
                fh.change::text as change
            FROM file_history fh
            LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
        )
        SELECT
            pv.id,
            jsonb_build_object(
                'added', COALESCE((SELECT jsonb_agg(file) FROM history WHERE version_id = pv.id AND change = 'create'), '[]'::jsonb),
                'updated', COALESCE((SELECT jsonb_agg(file) FROM history WHERE version_id = pv.id AND (change = 'update' OR change = 'update_diff')), '[]'::jsonb),
                'removed', COALESCE((SELECT jsonb_agg(file) FROM history WHERE version_id = pv.id AND change = 'delete'), '[]'::jsonb),
                'renamed', '[]'::jsonb
            ) AS changes
        FROM project_version pv
    )
    UPDATE project_version pv
    SET changes = ch.changes
    FROM changes ch
    WHERE ch.id = pv.id;
    """

    project_files_query = """
        UPDATE project p
        SET files = pv.files
        FROM project_version pv
        WHERE pv.project_id = p.id and p.latest_version = pv.name
    """

    removed_projects_files_query = """
    UPDATE project
    SET files = NULL
    WHERE storage_params IS NULL
    """
    conn.execute(sa.text(first_version_files_query))
    conn.execute(sa.text(version_files_query))
    conn.execute(sa.text(version_changes_query))
    conn.execute(sa.text(project_files_query))
    conn.execute(sa.text(removed_projects_files_query))


def downgrade():
    conn = op.get_bind()
    op.add_column(
        "project_version",
        sa.Column(
            "changes",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
            server_default="{}",
        ),
    )
    op.add_column(
        "project_version",
        sa.Column(
            "files",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
            server_default="[]",
        ),
    )
    op.drop_constraint(
        op.f("uq_project_version_project_id"), "project_version", type_="unique"
    )
    op.create_unique_constraint(
        "uq_project_id_version", "project_version", ["project_id", "name"]
    )
    op.create_index(
        "ix_project_version_files_gin",
        "project_version",
        ["files"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_project_version_changes_gin",
        "project_version",
        ["changes"],
        unique=False,
        postgresql_using="gin",
    )

    op.add_column(
        "project",
        sa.Column(
            "files",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
            server_default="[]",
        ),
    )
    op.create_index(
        "ix_project_files_gin",
        "project",
        ["files"],
        unique=False,
        postgresql_using="gin",
    )

    data_downgrade()
    # convert to string with 'v' prefix
    conn.execute(
        sa.text(
            "ALTER TABLE project ALTER COLUMN latest_version SET DATA TYPE VARCHAR USING 'v' || latest_version;"
        )
    )
    conn.execute(
        sa.text(
            "ALTER TABLE project_version ALTER COLUMN name SET DATA TYPE VARCHAR USING 'v' || name;"
        )
    )

    op.drop_index(op.f("ix_file_history_version_id"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_path"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_change"), table_name="file_history")
    op.drop_table("file_history")
    conn.execute(sa.text("DROP TYPE IF EXISTS push_change_type;"))
