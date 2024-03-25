"""project_version_unique

Revision ID: 90ee95d638f1
Revises: 6bd17a6b8707
Create Date: 2024-02-23 08:46:22.087477

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "90ee95d638f1"
down_revision = "6bd17a6b8707"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_project_id_version", "project_version", ["project_id", "name"]
    )


def downgrade():
    op.drop_constraint(op.f("uq_project_id_version"), "project_version", type_="unique")
