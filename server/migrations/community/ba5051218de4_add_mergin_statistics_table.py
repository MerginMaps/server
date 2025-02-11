"""add mergin statistics table

Revision ID: ba5051218de4
Revises: d02961c7416c
Create Date: 2025-01-24 12:41:23.714579

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ba5051218de4"
down_revision = "d02961c7416c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mergin_statistics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mergin_statistics")),
    )
    op.create_index(
        op.f("ix_mergin_statistics_created_at"),
        "mergin_statistics",
        ["created_at"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_index(
        op.f("ix_mergin_statistics_created_at"), table_name="mergin_statistics"
    )
    op.drop_table("mergin_statistics")
