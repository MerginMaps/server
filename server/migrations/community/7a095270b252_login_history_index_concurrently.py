"""Create login_history user/successful/timestamp index concurrently

CONCURRENTLY avoids blocking writes to login_history during the build
(every login attempt writes here), at the cost of running outside the
migration's transaction (autocommit_block) and leaving an INVALID index
behind on failure - upgrade()/downgrade() self-heal by dropping that first.

Revision ID: 7a095270b252
Revises: a3c8f2e1d947
Create Date: 2026-07-24 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7a095270b252"
down_revision = "a3c8f2e1d947"
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_login_history_user_id_successful_timestamp"
        )
        op.create_index(
            "ix_login_history_user_id_successful_timestamp",
            "login_history",
            ["user_id", "successful", "timestamp"],
            postgresql_concurrently=True,
        )


def downgrade():
    with op.get_context().autocommit_block():
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_login_history_user_id_successful_timestamp"
        )
