"""Create case insensitive unique indices

Revision ID: 07f2185e2428
Revises: 0e3fc92aeaaa
Create Date: 2024-05-21 10:02:07.808407

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "07f2185e2428"
down_revision = "0e3fc92aeaaa"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        "CREATE UNIQUE INDEX ix_username_insensitive_unique ON public.user (LOWER(username));"
    )
    conn.execute(
        "CREATE UNIQUE INDEX ix_email_insensitive_unique ON public.user (LOWER(email));"
    )


def downgrade():
    conn = op.get_bind()
    conn.execute("DROP INDEX IF EXISTS ix_username_insensitive_unique;")
    conn.execute("DROP INDEX IF EXISTS ix_email_insensitive_unique;")
