"""Add project member table

Revision ID: d02961c7416c
Revises: 1ab5b02ce532
Create Date: 2024-10-31 15:20:52.833051

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d02961c7416c"
down_revision = "1ab5b02ce532"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS intarray;"))

    op.create_table(
        "project_member",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("reader", "editor", "writer", "owner", name="project_role"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_project_member_project_id_project"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_project_member_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "project_id", "user_id", name=op.f("pk_project_member")
        ),
    )

    op.add_column("project", sa.Column("public", sa.Boolean(), nullable=True))

    data_upgrade()

    op.alter_column("project", "public", nullable=False)
    op.create_index(op.f("ix_project_public"), "project", ["public"], unique=False)
    op.drop_table("project_access")


def downgrade():
    op.create_table(
        "project_access",
        sa.Column("public", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column(
            "owners",
            postgresql.ARRAY(sa.INTEGER()),
            server_default=sa.text("'{}'::integer[]"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "readers",
            postgresql.ARRAY(sa.INTEGER()),
            server_default=sa.text("'{}'::integer[]"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "writers",
            postgresql.ARRAY(sa.INTEGER()),
            server_default=sa.text("'{}'::integer[]"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("project_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "editors",
            postgresql.ARRAY(sa.INTEGER()),
            server_default=sa.text("'{}'::integer[]"),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name="fk_project_access_project_id_project",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("project_id", name="pk_project_access"),
    )

    data_downgrade()

    op.create_index(
        "ix_project_access_writers",
        "project_access",
        ["writers"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_project_access_readers",
        "project_access",
        ["readers"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_project_access_public", "project_access", ["public"], unique=False
    )
    op.create_index(
        "ix_project_access_project_id", "project_access", ["project_id"], unique=False
    )
    op.create_index(
        "ix_project_access_owners",
        "project_access",
        ["owners"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_project_access_editors",
        "project_access",
        ["editors"],
        unique=False,
        postgresql_using="gin",
    )

    op.drop_index(op.f("ix_project_public"), table_name="project")
    op.drop_column("project", "public")
    op.drop_table("project_member")
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE project_role;"))


def data_upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            WITH members AS (
                SELECT
                        project_id AS project_id,
                        unnest(owners) AS user_id,
                        'owner' AS role
                FROM project_access
                UNION
                SELECT
                        project_id AS project_id,
                        unnest(writers - owners) AS user_id,
                        'writer' AS role
                FROM project_access
                UNION
                SELECT
                        project_id AS project_id,
                        unnest(editors - writers - owners) AS user_id,
                        'editor' AS role
                FROM project_access
                UNION
                SELECT
                        project_id AS project_id,
                        unnest(readers - editors - writers - owners) AS user_id,
                        'reader' AS role
                FROM project_access
            )
            INSERT INTO project_member (project_id, user_id, role)
            SELECT m.workspace_id, m.user_id, m.role::workspace_role
            FROM members m
            LEFT OUTER JOIN "user" u on u.id = m.user_id
            LEFT OUTER JOIN project p ON p.id = m.project_id
            WHERE
                u.username !~ 'deleted_\d{13}$' AND
                p.removed_at IS NULL;
        """
        )
    )

    conn.execute(
        sa.text(
            """
            UPDATE project p
            SET
                public = coalesce(pa.public, 'false')
            FROM project_access pa
            WHERE pa.project_id = p.id;
        """
        )
    )


def data_downgrade():
    conn = op.get_bind()
    # recreate 1:1 relationship for project
    conn.execute(
        sa.text(
            """
            INSERT INTO project_access (project_id, public)
            SELECT id, coalesce(public, 'false') FROM project;
        """
        )
    )

    # update access fields from assigned roles
    conn.execute(
        sa.text(
            """
            WITH members AS (
                WITH agg AS (
                    SELECT
                        project_id,
                        array_agg(user_id) AS users_ids,
                        role
                    FROM
                        project_member
                    GROUP BY project_id, role
                )
                SELECT
                    p.id AS project_id,
                    COALESCE(o.users_ids, '{}'::INT[]) AS owners,
                    COALESCE(o.users_ids || w.users_ids, '{}'::INT[]) AS writers,
                    COALESCE(o.users_ids || w.users_ids || e.users_ids, '{}'::INT[]) AS editors,
                    COALESCE(o.users_ids || w.users_ids || e.users_ids || r.users_ids, '{}'::INT[]) AS readers
                FROM project p
				LEFT OUTER JOIN (SELECT * FROM agg WHERE role = 'owner') AS o ON p.id = o.project_id
                LEFT OUTER JOIN (SELECT * FROM agg WHERE role = 'reader') AS r ON p.id = r.project_id
                LEFT OUTER JOIN (SELECT * FROM agg WHERE role = 'editor') AS e ON p.id = e.project_id
                LEFT OUTER JOIN (SELECT * FROM agg WHERE role = 'writer') AS w ON p.id = w.project_id
                )
            UPDATE project_access pa
            SET
                owners = m.owners,
                writers = m.writers,
                editors = m.editors,
                readers = m.readers
            FROM members m
            WHERE m.project_id = pa.project_id;
        """
        )
    )
