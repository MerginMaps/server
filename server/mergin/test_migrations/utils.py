# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import downgrade, upgrade
from pathlib import Path
from sqlalchemy import create_engine, make_url, text

# create_simple_app and Configuration are imported lazily inside their respective
# factory functions to avoid triggering Configuration evaluation at module import
# time (before pytest-dotenv has loaded .test.env into os.environ).

_STRUCTURAL_DIFF_TYPES = (
    "add_table",
    "remove_table",
    "add_column",
    "remove_column",
    "modify_nullable",
    "add_index",
    "remove_index",
    "add_constraint",
    "remove_constraint",
)


def assert_schema_consistent(engine, metadata, include_schemas=()):
    """Assert ORM metadata matches the migrated schema — structural checks only.

    Column types and server defaults are excluded: alembic's reflection of
    PostgreSQL-specific types (JSONB, UUID, ARRAY …) and default expressions
    produces false positives without an explicit allowlist.

    include_schemas: additional PostgreSQL schemas beyond 'public' to verify.
    Extra schemas are checked via direct inspection (table existence only) rather
    than compare_metadata, because include_schemas=True in MigrationContext causes
    public-schema tables to be reflected with an explicit "public" qualifier that
    doesn't match ORM models with schema=None — producing spurious add_table diffs.
    """
    from sqlalchemy import inspect as sa_inspect

    extra_schema_set = set(include_schemas)

    def _table_schema(d):
        """Extract the schema from a diff entry, or None."""
        if len(d) < 2:
            return None
        obj = d[1]
        # add_table / remove_table: obj is the Table
        schema = getattr(obj, "schema", None)
        if schema is not None:
            return schema
        # add_index / remove_index: obj is an Index whose .table has the schema
        table = getattr(obj, "table", None)
        return getattr(table, "schema", None)

    # Standard structural check for the public (default) schema.
    # Diffs involving tables in extra schemas are excluded here — they are
    # checked separately below via direct inspection to avoid the schema-name
    # mismatch that include_schemas=True causes in compare_metadata.
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        diff = compare_metadata(ctx, metadata)
    checked = [
        d
        for d in diff
        if d[0] in _STRUCTURAL_DIFF_TYPES and _table_schema(d) not in extra_schema_set
    ]

    # Table-existence check for each additional schema
    if include_schemas:
        inspector = sa_inspect(engine)
        for schema in include_schemas:
            existing = set(inspector.get_table_names(schema=schema))
            expected = {
                table.name
                for table in metadata.tables.values()
                if table.schema == schema
            }
            for name in sorted(expected - existing):
                checked.append(("add_table", f"{schema}.{name}"))
            for name in sorted(existing - expected):
                checked.append(("remove_table", f"{schema}.{name}"))

    assert not checked, (
        "ORM models differ from the migrated schema — add a migration or update the filter:\n"
        + "\n".join(str(d) for d in checked)
    )


def ordered_revisions(migrations_dir, head="head", version_locations=None):
    """Return revision IDs in upgrade order (base → head).

    Works for single-head (CE), single branch label (enterprise@head), and
    multi-head tuples (("enterprise@head", "service@head")) alembic setups.
    Pass version_locations as a colon-separated string when the script directory
    has more than one branch folder.
    """
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", migrations_dir)
    cfg.set_main_option(
        "version_locations",
        version_locations or str(Path(migrations_dir) / "community"),
    )
    cfg.set_main_option("path_separator", "os")
    script = ScriptDirectory.from_config(cfg)
    upper = tuple(head) if isinstance(head, (list, tuple)) else head
    return [
        rev.revision
        for rev in reversed(list(script.iterate_revisions(upper=upper, lower="base")))
    ]


def make_migration_app(extra_config=None, model_modules=()):
    """Return a module-scoped pytest fixture that provides a minimal Flask app context.

    The app context is all alembic's env.py needs: it reads SQLALCHEMY_DATABASE_URI
    from current_app.config and db metadata from Flask-Migrate's extension.

    model_modules: sequence of dotted module paths to import when the fixture runs,
    e.g. ["mergin.sync.models", "src.workspace.models"].  Importing here (inside the
    fixture) rather than at test-module level avoids db.metadata cross-contamination
    when multiple migration test files are collected in the same pytest session: models
    are only added to db.metadata when the fixture first executes, not at collection time.

    extra_config: optional dict of additional config values to set on the app.
    Use this when a migration reads from current_app.config for non-DB settings.
    """

    @pytest.fixture(scope="module")
    def migration_app(migration_engine):
        import importlib

        from ..app import create_simple_app

        for module_path in model_modules:
            importlib.import_module(module_path)

        app = create_simple_app()
        app.config["SQLALCHEMY_DATABASE_URI"] = migration_engine.url.render_as_string(
            hide_password=False
        )
        if extra_config:
            app.config.update(extra_config)
        ctx = app.app_context()
        ctx.push()
        try:
            yield app
        finally:
            ctx.pop()

    return migration_app


def make_migration_engine(test_db_name, pre_migration_sql=()):
    """Return a module-scoped pytest fixture that creates and tears down a migration test DB.

    pre_migration_sql: optional sequence of SQL statements executed once after the DB
    is created but before any migration runs (e.g. CREATE SCHEMA, CREATE EXTENSION).
    """

    @pytest.fixture(scope="module")
    def migration_engine():
        from ..config import Configuration

        base_url = make_url(Configuration.SQLALCHEMY_DATABASE_URI)
        admin_url = base_url.set(database="postgres")
        test_db_url = base_url.set(database=test_db_name)

        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
        admin_engine.dispose()

        engine = create_engine(test_db_url)
        if pre_migration_sql:
            with engine.connect() as conn:
                for sql in pre_migration_sql:
                    conn.execute(text(sql))
                conn.commit()

        yield engine
        engine.dispose()

        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        admin_engine.dispose()

    return migration_engine


def run_migration_lifecycle(
    engine, migrations_dir, revisions, metadata, downgrade_targets, include_schemas=()
):
    """Run the three-phase migration lifecycle used by all migration test suites.

    Phase 1 — upgrade one revision at a time, asserting alembic_version after each.
              Works for both single-head and multi-head chains: the applied-versions
              set is checked with `in` so interleaved branch revisions pass correctly.
    Phase 2 — structural schema consistency check between ORM metadata and the migrated DB.
    Phase 3 — downgrade to each target in downgrade_targets (str or list[str]),
              asserting the final alembic_version set matches exactly.
    """
    assert (
        revisions
    ), "ordered_revisions returned an empty list — check migrations_dir and version_locations"
    for rev in revisions:
        upgrade(directory=migrations_dir, revision=rev)
        with engine.connect() as conn:
            applied = {
                row[0]
                for row in conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchall()
            }
        assert (
            rev in applied
        ), f"Migration {rev} did not apply correctly: alembic_version is {applied!r}"

    assert_schema_consistent(engine, metadata, include_schemas)

    if isinstance(downgrade_targets, str):
        downgrade_targets = [downgrade_targets]
    for target in downgrade_targets:
        downgrade(directory=migrations_dir, revision=target)
    with engine.connect() as conn:
        final = {
            row[0]
            for row in conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).fetchall()
        }
    assert final == set(
        downgrade_targets
    ), f"Unexpected state after downgrade: {final!r}"
