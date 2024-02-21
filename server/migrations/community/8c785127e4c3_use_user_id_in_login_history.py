# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
"""use user_id in login history

Revision ID: 8c785127e4c3
Revises: 6bd17a6b8707
Create Date: 2024-02-21 08:28:00.731970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8c785127e4c3"
down_revision = "6bd17a6b8707"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("login_history", sa.Column("user_id", sa.Integer(), nullable=True))
    op.drop_index("ix_login_history_username", table_name="login_history")
    op.create_index(
        op.f("ix_login_history_user_id"), "login_history", ["user_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_login_history_user_id_user"),
        "login_history",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE login_history lh
            SET user_id = u.id
            FROM public."user" u
            WHERE u.username = lh.username
            """
        )
    )

    op.drop_column("login_history", "username")


def downgrade():
    op.add_column(
        "login_history",
        sa.Column("username", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_login_history_username", "login_history", ["username"], unique=False
    )

    # data migration
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE login_history lh
            SET username = u.username
            FROM public."user" u
            WHERE u.id = lh.user_id
            """
        )
    )

    op.drop_constraint(
        op.f("fk_login_history_user_id_user"), "login_history", type_="foreignkey"
    )
    op.drop_index(op.f("ix_login_history_user_id"), table_name="login_history")
    op.drop_column("login_history", "user_id")
