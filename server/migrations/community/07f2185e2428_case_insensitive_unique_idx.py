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
        "CREATE UNIQUE INDEX ix_user_username ON public.user (LOWER(username));"
    )
    conn.execute("CREATE UNIQUE INDEX ix_email_username ON public.user (LOWER(email));")
    conn.execute("ALTER TABLE public.user DROP CONSTRAINT uq_user_email;")
    conn.execute("ALTER TABLE public.user DROP CONSTRAINT uq_user_username;")


def downgrade():
    conn = op.get_bind()
    conn.execute("DROP INDEX IF EXISTS ix_user_username;")
    conn.execute("DROP INDEX IF EXISTS ix_email_username;")
    conn.execute("ALTER TABLE public.user ADD CONSTRAINT uq_user_email UNIQUE (email);")
    conn.execute(
        "ALTER TABLE public.user ADD CONSTRAINT uq_user_username UNIQUE (username);"
    )
