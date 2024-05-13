"""add editors

Revision ID: 54c2c49fe2c7
Revises: 0e3fc92aeaaa
Create Date: 2024-05-13 14:13:42.985827

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "54c2c49fe2c7"
down_revision = "0e3fc92aeaaa"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "project_access",
        sa.Column(
            "editors",
            postgresql.ARRAY(sa.Integer()),
            server_default="{}",
            nullable=True,
        ),
    )
    op.create_index(
        "ix_project_access_editors",
        "project_access",
        ["editors"],
        unique=False,
        postgresql_using="gin",
    )

    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE project_access
            SET editors = writers
            """
        )
    )


def downgrade():
    op.drop_index(
        "ix_project_access_editors", table_name="project_access", postgresql_using="gin"
    )
    op.drop_column("project_access", "editors")
