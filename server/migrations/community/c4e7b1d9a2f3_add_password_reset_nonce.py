"""Add password_reset_nonce to user table

Revision ID: c4e7b1d9a2f3
Revises: 7a095270b252
Create Date: 2026-09-29 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4e7b1d9a2f3"
down_revision = "7a095270b252"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("password_reset_nonce", sa.String(64), nullable=True),
    )


def downgrade():
    op.drop_column("user", "password_reset_nonce")
