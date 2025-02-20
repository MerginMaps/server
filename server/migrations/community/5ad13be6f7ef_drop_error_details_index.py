"""Drop error details index

Revision ID: 5ad13be6f7ef
Revises: ba5051218de4
Create Date: 2025-02-20 07:52:36.670158

"""
from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision = '5ad13be6f7ef'
down_revision = 'ba5051218de4'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
                DROP INDEX IF EXISTS ix_sync_failures_history_error_details;
            """
        )
    )


def downgrade():
    op.create_index(op.f('ix_sync_failures_history_error_details'), 'sync_failures_history', ['error_details'],
                    unique=False)
