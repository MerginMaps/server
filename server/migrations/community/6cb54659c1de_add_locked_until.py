"""Add locked_until to project

Revision ID: 6cb54659c1de
Revises: 5ad13be6f7ef
Create Date: 2025-04-10 11:11:09.277522

"""

from alembic import op
import sqlalchemy as sa


revision = "6cb54659c1de"
down_revision = "5ad13be6f7ef"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("project", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_project_locked_until"), "project", ["locked_until"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_project_locked_until"), table_name="project")
    op.drop_column("project", "locked_until")
