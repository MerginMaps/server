"""Add user last signed in

Revision ID: b9ec9ab6694f
Revises: 6cb54659c1de
Create Date: 2025-09-09 15:43:19.554498

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b9ec9ab6694f"
down_revision = "6cb54659c1de"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("last_signed_in", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("user", "last_signed_in")
