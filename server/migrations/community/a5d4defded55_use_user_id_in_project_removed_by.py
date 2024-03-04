"""use user id in project removed by

Revision ID: a5d4defded55
Revises: 46fedf98dca5
Create Date: 2024-02-27 12:55:59.743264

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5d4defded55"
down_revision = "46fedf98dca5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_project_removed_by", table_name="project")
    # rename original column to keep for data migration
    op.alter_column(
        "project", "removed_by", nullable=True, new_column_name="removed_by_username"
    )
    op.add_column("project", sa.Column("removed_by", sa.Integer(), nullable=True))

    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE project p
            SET removed_by = u.id
            FROM public."user" u
            WHERE u.username = p.removed_by_username
            """
        )
    )
    op.drop_column("project", "removed_by_username")
    op.create_foreign_key(
        op.f("fk_project_removed_by_user"), "project", "user", ["removed_by"], ["id"]
    )
    op.create_index(
        op.f("ix_project_removed_by"),
        "project",
        ["removed_by"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_project_removed_by", table_name="project")
    op.alter_column(
        "project", "removed_by", nullable=True, new_column_name="removed_by_id"
    )
    op.add_column("project", sa.Column("removed_by", sa.String(), nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE project p
            SET removed_by = u.username
            FROM public."user" u
            WHERE u.id = p.removed_by_id
            """
        )
    )
    op.drop_constraint("fk_project_removed_by_user", "project", type_="foreignkey")
    op.drop_column("project", "removed_by_id")
    op.create_index(
        op.f("ix_project_removed_by"),
        "project",
        ["removed_by"],
        unique=False,
    )
