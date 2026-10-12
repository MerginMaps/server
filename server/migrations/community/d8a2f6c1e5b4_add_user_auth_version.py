"""Add auth_version to user table

Revision ID: d8a2f6c1e5b4
Revises: c4e7b1d9a2f3
Create Date: 2026-10-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8a2f6c1e5b4"
down_revision = "c4e7b1d9a2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("user", "auth_version")
