"""Add last_ping to upload

Revision ID: e3a7f2b1c94d
Revises: e3f1a9b2c4d6
Create Date: 2026-04-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3a7f2b1c94d"
down_revision = "e3f1a9b2c4d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("upload", sa.Column("last_ping", sa.DateTime(), nullable=True))
    # backfill existing rows before adding NOT NULL constraint
    op.execute("UPDATE upload SET last_ping = NOW() WHERE last_ping IS NULL")
    op.alter_column("upload", "last_ping", nullable=False)


def downgrade():
    # drop the column but required lockfiles will be missing - make sure all uploads are gone
    op.drop_column("upload", "last_ping")
