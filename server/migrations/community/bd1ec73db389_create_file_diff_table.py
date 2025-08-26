"""create file diff table

Revision ID: bd1ec73db389
Revises: 6cb54659c1de
Create Date: 2025-07-17 14:17:02.373645

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bd1ec73db389"
down_revision = "6cb54659c1de"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "file_diff",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("file_path_id", sa.BigInteger(), nullable=False),
        sa.Column("basefile_id", sa.BigInteger(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["basefile_id"],
            ["file_history.id"],
            name=op.f("fk_file_diff_basefile_id_file_history"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_path_id"],
            ["project_file_path.id"],
            name=op.f("fk_file_diff_file_path_id_project_file_path"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_diff")),
        sa.UniqueConstraint("file_path_id", "rank", "version", name="unique_diff"),
    )
    op.create_index(
        op.f("ix_file_diff_basefile_id"), "file_diff", ["basefile_id"], unique=False
    )
    op.create_index(
        "ix_file_diff_file_path_id_version_rank",
        "file_diff",
        ["file_path_id", "version", "rank"],
        unique=False,
    )
    op.create_index(op.f("ix_file_diff_path"), "file_diff", ["path"], unique=False)
    op.create_index(op.f("ix_file_diff_rank"), "file_diff", ["rank"], unique=False)
    op.create_index(
        op.f("ix_file_diff_version"), "file_diff", ["version"], unique=False
    )

    # migrate data
    conn = op.get_bind()
    conn.execute(
        """
        WITH diffs AS (
            SELECT * 
            FROM file_history 
            WHERE diff IS NOT NULL
        ),
        basefiles AS (
            SELECT DISTINCT 
                fh.id AS basefile_id, 
                fh.file_path_id,
                fh.project_version_name AS basefile_version
            FROM diffs d
            LEFT OUTER JOIN file_history fh ON fh.file_path_id = d.file_path_id
            WHERE 
                fh.change = ANY(ARRAY['create'::push_change_type, 'update'::push_change_type])
        ),
        relevant_basefiles AS (
            SELECT 
                d.id, 
                d.project_version_name, 
                b.basefile_id, 
                b.basefile_version
            FROM diffs d
            LEFT OUTER JOIN basefiles b ON b.file_path_id = d.file_path_id AND b.basefile_version < d.project_version_name
        )    
        INSERT INTO file_diff (file_path_id, basefile_id, rank, version, path, size, checksum, location)
        SELECT DISTINCT
            d.file_path_id,
            FIRST_VALUE(rb.basefile_id) OVER (PARTITION BY rb.id ORDER BY rb.basefile_version DESC) as basefile_id,
            0 AS rank,
            d.project_version_name AS version,
            (d.diff ->> 'path') AS path,
            (d.diff ->> 'size')::bigint AS size,
            d.diff ->> 'checksum' AS checksum,
            d.diff ->> 'location' AS location
        FROM diffs d
        LEFT OUTER JOIN relevant_basefiles rb ON rb.id = d.id;
        """
    )

    op.drop_column("file_history", "diff")


def downgrade():
    op.add_column(
        "file_history",
        sa.Column(
            "diff",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )

    # migrate data
    conn = op.get_bind()
    conn.execute(
        """
        UPDATE file_history fh
        SET diff = jsonb_build_object(
            'path', fd.path,
            'size', fd.size,
            'checksum', fd.checksum,
            'location', fd.location
        )
        FROM file_diff fd
        WHERE fh.file_path_id = fd.file_path_id AND fh.project_version_name = fd.version AND fd.rank = 0;
        """
    )

    op.drop_index(op.f("ix_file_diff_version"), table_name="file_diff")
    op.drop_index(op.f("ix_file_diff_rank"), table_name="file_diff")
    op.drop_index(op.f("ix_file_diff_path"), table_name="file_diff")
    op.drop_index("ix_file_diff_file_path_id_version_rank", table_name="file_diff")
    op.drop_index(op.f("ix_file_diff_basefile_id"), table_name="file_diff")
    op.drop_table("file_diff")
