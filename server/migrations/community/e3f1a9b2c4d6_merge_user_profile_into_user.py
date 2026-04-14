# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Merge user_profile table into user table

Revision ID: e3f1a9b2c4d6
Revises: 4b4648483770
Create Date: 2026-04-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "e3f1a9b2c4d6"
down_revision = "4b4648483770"
branch_labels = None
depends_on = None


def upgrade():
    # Add profile columns to user table (nullable initially to allow data copy)
    op.add_column(
        "user", sa.Column("receive_notifications", sa.Boolean(), nullable=True)
    )
    op.add_column("user", sa.Column("first_name", sa.String(256), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.String(256), nullable=True))

    # Copy data from user_profile
    op.execute(
        """
        UPDATE "user" u
        SET 
            receive_notifications = up.receive_notifications,
            first_name            = up.first_name,
            last_name             = up.last_name
        FROM user_profile up
        WHERE up.user_id = u.id;
        """
    )

    # Fill in default for any users without a profile row (should not exist, but be safe)
    op.execute(
        'UPDATE "user" SET receive_notifications = TRUE WHERE receive_notifications IS NULL;'
    )

    op.alter_column("user", "receive_notifications", nullable=False)
    op.create_index("ix_user_receive_notifications", "user", ["receive_notifications"])
    op.drop_table("user_profile")


def downgrade():
    # Recreate user_profile table
    op.create_table(
        "user_profile",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("receive_notifications", sa.Boolean(), nullable=False),
        sa.Column("first_name", sa.String(256), nullable=True),
        sa.Column("last_name", sa.String(256), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # Copy data back
    op.execute(
        """
        INSERT INTO user_profile (user_id, receive_notifications, first_name, last_name)
        SELECT id, receive_notifications, first_name, last_name
        FROM "user";
        """
    )

    op.create_index(
        "ix_user_profile_receive_notifications",
        "user_profile",
        ["receive_notifications"],
    )

    # Remove columns from user table
    op.drop_index("ix_user_receive_notifications", table_name="user")
    op.drop_column("user", "receive_notifications")
    op.drop_column("user", "first_name")
    op.drop_column("user", "last_name")
