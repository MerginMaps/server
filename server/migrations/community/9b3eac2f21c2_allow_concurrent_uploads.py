"""Allow concurrent uploads

Create partial index to limit at most one blocking upload per project.

Revision ID: 9b3eac2f21c2
Revises: 6cb54659c1de
Create Date: 2025-06-10 14:00:30.094460

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b3eac2f21c2"
down_revision = "6cb54659c1de"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("upload", sa.Column("blocking", sa.Boolean(), nullable=True))
    op.drop_index("ix_upload_version", table_name="upload")
    op.drop_constraint("uq_upload_project_id", "upload", type_="unique")
    op.create_index(
        "ix_upload_blocking_partial",
        "upload",
        ["project_id", "blocking"],
        unique=True,
        postgresql_where=sa.text("blocking"),
    )
    op.drop_column("upload", "version")

    # data migration - set all current uploads to blocking
    conn = op.get_bind()
    query = """
        UPDATE upload
        SET blocking = true;
    """
    conn.execute(sa.text(query))


def downgrade():
    op.add_column(
        "upload", sa.Column("version", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.drop_index(
        "ix_upload_blocking_partial",
        table_name="upload",
        postgresql_where=sa.text("blocking"),
    )

    # data migration - remove concurrent uploads, set upload version to project latest version
    conn = op.get_bind()
    remove_query = """
        WITH multiple_uploads AS (
            SELECT
                u.id,
            ROW_NUMBER() OVER(
                PARTITION BY u.project_id
                ORDER BY u.created asc 
            ) AS row_number
            FROM upload u
            INNER JOIN project p ON p.id = u.project_id
        )
        DELETE FROM upload u
        USING multiple_uploads mu
        WHERE u.id = mu.id AND mu.row_number > 1;
    """
    conn.execute(sa.text(remove_query))

    update_query = """
        UPDATE upload u
        SET version = p.latest_version
        FROM project p
        WHERE p.id = u.project_id;
    """
    conn.execute(sa.text(update_query))

    op.create_unique_constraint(
        "uq_upload_project_id", "upload", ["project_id", "version"]
    )
    op.create_index("ix_upload_version", "upload", ["version"], unique=False)
    op.drop_column("upload", "blocking")
