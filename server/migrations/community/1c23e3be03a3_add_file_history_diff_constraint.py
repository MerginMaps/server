"""Add file history diff constraint

Revision ID: 1c23e3be03a3
Revises: 57d0de13ce4a
Create Date: 2024-09-09 09:46:42.950624

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1c23e3be03a3"
down_revision = "57d0de13ce4a"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
                UPDATE file_history
                SET diff = NULL
                WHERE change != 'update_diff' AND diff IS NOT NULL;
                """
        )
    )
    conn.execute(
        sa.text(
            """
            ALTER TABLE file_history
            ADD CONSTRAINT ck_file_history_changes_with_diff CHECK (
                CASE
                    WHEN (change = 'update_diff') THEN diff IS NOT NULL
                    ELSE diff IS NULL
                END
            );
            """
        )
    )


def downgrade():
    op.drop_constraint(
        op.f("ck_file_history_changes_with_diff"),
        "file_history",
    )
