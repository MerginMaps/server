"""Add locked_until to user table and successful flag to login_history

Revision ID: a3c8f2e1d947
Revises: f1d9e4a7b823
Create Date: 2026-06-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3c8f2e1d947"
down_revision = "f1d9e4a7b823"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "locked_until",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "login_history",
        sa.Column(
            "successful",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade():
    op.drop_column("login_history", "successful")
    op.drop_column("user", "locked_until")
