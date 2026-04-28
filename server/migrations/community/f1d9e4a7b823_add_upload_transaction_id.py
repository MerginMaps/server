"""Add transaction_id to upload

Revision ID: f1d9e4a7b823
Revises: e3a7f2b1c94d
Create Date: 2026-04-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "f1d9e4a7b823"
down_revision = "e3a7f2b1c94d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "upload", sa.Column("transaction_id", UUID(as_uuid=True), nullable=True)
    )
    # backfill existing rows before adding NOT NULL constraint
    op.execute("UPDATE upload SET transaction_id = id WHERE transaction_id IS NULL")
    op.alter_column("upload", "transaction_id", nullable=False)
    op.create_index(
        op.f("ix_upload_transaction_id"), "upload", ["transaction_id"], unique=True
    )


def downgrade():
    op.drop_index(op.f("ix_upload_transaction_id"), table_name="upload")
    # column is dropped but there could be orphan transaction folders, make sure upload table is empty
    op.drop_column("upload", "transaction_id")
