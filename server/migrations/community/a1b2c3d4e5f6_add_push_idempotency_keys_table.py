"""Add push_idempotency_keys table

Revision ID: a1b2c3d4e5f6
Revises: f1d9e4a7b823
Create Date: 2026-05-19 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f1d9e4a7b823"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "push_idempotency_keys",
        sa.Column("key", UUID(), nullable=False),
        sa.Column("response", JSONB(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index(
        op.f("ix_push_idempotency_keys_created"),
        "push_idempotency_keys",
        ["created"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_push_idempotency_keys_created"), table_name="push_idempotency_keys"
    )
    op.drop_table("push_idempotency_keys")
