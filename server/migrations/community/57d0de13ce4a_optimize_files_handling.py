"""Optimize files handling: introduce project_file_path and latest_project_files tables

Revision ID: 57d0de13ce4a
Revises: c13819c566e7
Create Date: 2024-08-09 07:59:43.260401

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "57d0de13ce4a"
down_revision = "c13819c566e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_project_version_project_id_name",
        "project_version",
        ["project_id", sa.text("name ASC NULLS LAST")],
        unique=False,
    )
    op.create_table(
        "latest_project_files",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_history_ids", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_latest_project_files_project_id_project"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("project_id", name=op.f("pk_latest_project_files")),
    )
    op.create_index(
        op.f("ix_latest_project_files_project_id"),
        "latest_project_files",
        ["project_id"],
        unique=False,
    )
    op.create_table(
        "project_file_path",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_project_file_path_project_id_project"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_file_path")),
        sa.UniqueConstraint(
            "project_id", "path", name=op.f("uq_project_file_path_project_id")
        ),
    )
    op.create_index(
        op.f("ix_project_file_path_project_id_path"),
        "project_file_path",
        ["project_id", "path"],
        unique=False,
    )
    op.add_column(
        "file_history", sa.Column("file_path_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "file_history", sa.Column("project_version_name", sa.Integer(), nullable=True)
    )
    op.drop_constraint("uq_file_history_version_id", "file_history", type_="unique")

    data_upgrade()

    op.create_index(
        "ix_file_history_file_path_id_project_version_name",
        "file_history",
        ["file_path_id", sa.text("project_version_name DESC")],
        unique=False,
    )
    # after data upgrade set columns to NOT NULL
    op.alter_column(
        "file_history", "file_path_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.alter_column(
        "file_history",
        "project_version_name",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_unique_constraint(
        op.f("uq_file_history_version_id"),
        "file_history",
        ["version_id", "file_path_id"],
    )
    op.create_foreign_key(
        op.f("fk_file_history_file_path_id_project_file_path"),
        "file_history",
        "project_file_path",
        ["file_path_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_index(
        "ix_file_history_file_path_id_project_version_name", table_name="file_history"
    )
    op.drop_column("file_history", "project_version_name")
    op.add_column(
        "file_history",
        sa.Column("path", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    data_downgrade()
    op.drop_index(
        op.f("ix_project_file_path_project_id_path"), table_name="project_file_path"
    )
    op.drop_index("ix_project_version_project_id_name", table_name="project_version")

    op.alter_column("file_history", "path", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_constraint(
        op.f("fk_file_history_file_path_id_project_file_path"),
        "file_history",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("uq_file_history_version_id"), "file_history", type_="unique"
    )
    op.create_unique_constraint(
        "uq_file_history_version_id", "file_history", ["version_id", "path"]
    )
    op.drop_column("file_history", "file_path_id")
    op.create_index("ix_file_history_path", "file_history", ["path"], unique=False)
    op.drop_table("project_file_path")
    op.drop_index(
        op.f("ix_latest_project_files_project_id"), table_name="latest_project_files"
    )
    op.drop_table("latest_project_files")


def data_upgrade():
    conn = op.get_bind()
    # extract file path from file_history to project_file_path
    conn.execute(
        sa.text(
            """
        INSERT INTO project_file_path (project_id, path)
        SELECT DISTINCT
            pv.project_id,
            path
        FROM
            file_history fh
        INNER JOIN project_version pv ON (pv.id = fh.version_id);
    """
        )
    )

    # update file_history table via temporary results
    conn.execute(
        sa.text(
            """
            CREATE TEMPORARY TABLE file_history_mig AS
                SELECT
                    fp.id AS file_path_id,
                    fh.id AS file_history_id,
                    pv.name AS version_name
                FROM
                    file_history fh
                    INNER JOIN project_version pv ON (pv.id = fh.version_id)
                    LEFT OUTER JOIN project_file_path fp ON (fp.project_id = pv.project_id AND fp.path = fh.path);

                CREATE INDEX mig_file_history_mig_file_path_id
                    ON file_history_mig (file_path_id);
        """
        )
    )

    # drop indexes for update speed up
    op.drop_index(op.f("ix_file_history_version_id"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_change"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_path"), table_name="file_history")
    op.drop_column("file_history", "path")

    conn.execute(
        sa.text(
            """
        UPDATE file_history
        SET
            file_path_id = mig.file_path_id,
            project_version_name = mig.version_name
        FROM file_history_mig mig
        WHERE file_history.id = mig.file_history_id;
        """
        )
    )

    # recreate indexes again
    op.create_index(
        op.f("ix_file_history_change"), "file_history", ["change"], unique=False
    )
    op.create_index(
        op.f("ix_file_history_version_id"), "file_history", ["version_id"], unique=False
    )

    # fill up latest_project_files for later caching
    conn.execute(
        sa.text(
            """
        INSERT INTO latest_project_files
        SELECT id AS project_id
        FROM project;
        """
        )
    )


def data_downgrade():
    # drop indexes for update speed up
    op.drop_index(op.f("ix_file_history_version_id"), table_name="file_history")
    op.drop_index(op.f("ix_file_history_change"), table_name="file_history")

    op.create_index(
        op.f("ix_file_history_file_path_id_mig"),
        "file_history",
        ["file_path_id"],
        unique=False,
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        UPDATE file_history fh
        SET path = pf.path
        FROM project_file_path pf
        WHERE pf.id = fh.file_path_id;
    """
        )
    )

    op.drop_index(op.f("ix_file_history_file_path_id_mig"), table_name="file_history")

    # recreate indexes again
    op.create_index(
        op.f("ix_file_history_change"), "file_history", ["change"], unique=False
    )
    op.create_index(
        op.f("ix_file_history_version_id"), "file_history", ["version_id"], unique=False
    )
