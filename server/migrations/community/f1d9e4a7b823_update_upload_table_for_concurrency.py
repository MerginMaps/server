"""Add transaction_id and last_ping columns to upload

Revision ID: f1d9e4a7b823
Revises: e3f1a9b2c4d6
Create Date: 2026-04-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "f1d9e4a7b823"
down_revision = "e3f1a9b2c4d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "upload", sa.Column("transaction_id", UUID(as_uuid=True), nullable=True)
    )
    op.add_column("upload", sa.Column("last_ping", sa.DateTime(), nullable=True))

    # backfill existing rows before adding NOT NULL constraint
    op.execute(
        "UPDATE upload SET transaction_id = id::uuid WHERE transaction_id IS NULL;"
    )
    op.execute("UPDATE upload SET last_ping = NOW() WHERE last_ping IS NULL;")

    op.alter_column("upload", "transaction_id", nullable=False)
    op.alter_column("upload", "last_ping", nullable=False)

    op.create_index(
        op.f("ix_upload_transaction_id"), "upload", ["transaction_id"], unique=True
    )


def downgrade():
    op.drop_index(op.f("ix_upload_transaction_id"), table_name="upload")
    # column is dropped but there could be orphan transaction folders and required lockfiles will be missing, make sure upload table is empty
    op.drop_column("upload", "transaction_id")
    op.drop_column("upload", "last_ping")
