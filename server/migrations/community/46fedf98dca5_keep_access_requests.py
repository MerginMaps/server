"""keep access requests, add tracking columns

Revision ID: 46fedf98dca5
Revises: 55fa7fcee893
Create Date: 2024-02-26 12:45:17.573103

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from mergin.sync.config import Configuration

# revision identifiers, used by Alembic.
revision = "46fedf98dca5"
down_revision = "55fa7fcee893"
branch_labels = None
depends_on = None

request_status_type = postgresql.ENUM("accepted", "declined", name="request_status")


def upgrade():
    request_status_type.create(op.get_bind())
    op.add_column(
        "access_request", sa.Column("requested_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "access_request", sa.Column("requested_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "access_request", sa.Column("resolved_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "access_request", sa.Column("resolved_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "access_request", sa.Column("status", request_status_type, nullable=True)
    )
    op.create_index(
        op.f("ix_access_request_requested_at"),
        "access_request",
        ["requested_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_request_resolved_at"),
        "access_request",
        ["resolved_at"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_access_request_resolved_by_user"),
        "access_request",
        "user",
        ["resolved_by"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_access_request_requested_by_user"),
        "access_request",
        "user",
        ["requested_by"],
        ["id"],
        ondelete="CASCADE",
    )

    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            f"""
            UPDATE public.access_request
            SET
                requested_by = user_id,
                requested_at = expire - interval '{Configuration.PROJECT_ACCESS_REQUEST} seconds'
            """
        )
    )
    op.alter_column("access_request", "requested_by", nullable=False)
    op.alter_column("access_request", "requested_at", nullable=False)

    op.drop_index("ix_access_request_user_id", table_name="access_request")
    op.drop_constraint(
        "fk_access_request_user_id_user", "access_request", type_="foreignkey"
    )
    op.drop_column("access_request", "expire")
    op.drop_column("access_request", "user_id")


def downgrade():
    op.add_column(
        "access_request",
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "access_request",
        sa.Column("expire", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "fk_access_request_user_id_user",
        "access_request",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_access_request_user_id", "access_request", ["user_id"], unique=False
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            f"""
                UPDATE public.access_request
                SET
                    user_id = requested_by,
                    expire = requested_at  + interval '{Configuration.PROJECT_ACCESS_REQUEST} seconds'
                """
        )
    )

    op.drop_constraint(
        op.f("fk_access_request_requested_by_user"),
        "access_request",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_access_request_resolved_by_user"), "access_request", type_="foreignkey"
    )
    op.drop_index(op.f("ix_access_request_resolved_at"), table_name="access_request")
    op.drop_index(op.f("ix_access_request_requested_at"), table_name="access_request")
    op.drop_column("access_request", "status")
    op.drop_column("access_request", "resolved_at")
    op.drop_column("access_request", "resolved_by")
    op.drop_column("access_request", "requested_at")
    op.drop_column("access_request", "requested_by")
    request_status_type.drop(op.get_bind())
