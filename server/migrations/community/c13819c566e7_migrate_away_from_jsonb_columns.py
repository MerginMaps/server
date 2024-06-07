"""Migrate away from jsonb columns in project and project_version tables, introduce new file history table

Revision ID: c13819c566e7
Revises: 07f2185e2428
Create Date: 2024-06-06 16:05:59.565541

"""

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
conn = op.get_bind()


def upgrade():
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

    op.drop_index("ix_project_files_gin", table_name="project", postgresql_using="gin")
    op.drop_column("project", "files")
    op.drop_index(
        "ix_project_version_changes_gin",
        table_name="project_version",
        postgresql_using="gin",
    )
    op.drop_index(
        "ix_project_version_files_gin",
        table_name="project_version",
        postgresql_using="gin",
    )
    op.drop_constraint("uq_project_id_version", "project_version", type_="unique")
    op.drop_column("project_version", "files")
    op.drop_column("project_version", "changes")

    op.create_unique_constraint(
        op.f("uq_project_version_project_id"), "project_version", ["project_id", "name"]
    )


def data_upgrade():
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
    # construct version files and changes, update project files with latest version files
    version_files_query = """
    WITH version_files AS (
        WITH files_ids AS (
            SELECT DISTINCT
            FIRST_VALUE (fh.id) OVER (
                    PARTITION BY fh.path
                    ORDER BY
                        pv.created DESC
                ) as pf_id
            FROM project_version pv
            LEFT OUTER JOIN file_history fh ON fh.version_id = pv.id
        )
        SELECT
            version_id,
            jsonb_agg(
                json_build_object(
                    'path', fh.path,
                    'size', fh.size,
                    'checksum', fh.checksum,
                    'diff', coalesce(fh.diff, '{}'),
                    'location', fh.location,
                    'sanitized_path', ltrim(fh.location, pv.name || '/')
                )
            ) AS files
        FROM file_history fh
        LEFT OUTER JOIN files_ids ON files_ids.pf_id = fh.id
        LEFT OUTER JOIN project_version pv ON pv.id = fh.version_id
        WHERE fh.change::text != 'delete'
        GROUP BY fh.version_id
    )
    UPDATE project_version pv
    SET files = vf.files
    FROM version_files vf
    WHERE vf.version_id = pv.id;
    """

    version_changes_query = """
    WITH changes AS (
        WITH change_preprocess AS (
            SELECT
                pv.id,
                jsonb_agg(
                    json_build_object(
                        'path', fh.path,
                        'size', fh.size,
                        'checksum', fh.checksum,
                        'diff', coalesce(fh.diff, '{}'),
                        'location', fh.location,
                        'sanitized_path', ltrim(fh.location, pv.name || '/')
                    )
                ) AS meta,
                fh.change
            FROM project_version pv
            LEFT JOIN file_history fh ON pv.id = fh.version_id
            GROUP BY pv.id, fh.change
        )
        SELECT
            id,
            CASE
                WHEN change::text = 'create' THEN meta
                ELSE '[]'::jsonb
            END AS added,
            CASE
                WHEN change::text = 'update' OR change::text = 'update_diff' THEN meta
                ELSE '[]'::jsonb
            END AS updated,
            CASE
                WHEN change::text = 'delete' THEN meta
                ELSE '[]'::jsonb
            END AS removed
        from change_preprocess
    )
    UPDATE project_version pv
    SET changes = json_build_object('added', added, 'updated', updated, 'removed', removed, 'renamed', '[]'::jsonb)
    FROM changes ch
    WHERE ch.id = pv.id;
    """

    project_files_query = """
    UPDATE project p
    SET files = pv.files
    FROM project_version pv
    WHERE pv.project_id = p.id and p.latest_version = pv.name
    """

    conn.execute(sa.text(version_files_query))
    conn.execute(sa.text(version_changes_query))
    conn.execute(sa.text(project_files_query))


def downgrade():
    op.add_column(
        "project_version",
        sa.Column(
            "changes",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "project_version",
        sa.Column(
            "files",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
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
        ),
    )
    op.create_index(
        "ix_project_files_gin",
        "project",
        ["files"],
        unique=False,
        postgresql_using="gin",
    )

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
    data_downgrade()

    op.drop_index(op.f("ix_file_history_version_id"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_path"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_change"), table_name="file_history")
    op.drop_table("file_history")
    conn.execute(sa.text("DROP TYPE IF EXISTS push_change_type;"))
