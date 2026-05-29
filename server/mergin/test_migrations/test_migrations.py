# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from pathlib import Path

from ..app import db
from .utils import (
    make_migration_app,
    make_migration_engine,
    ordered_revisions,
    run_migration_lifecycle,
)

MIGRATIONS_DIR = str(Path(__file__).parents[2] / "migrations")
# 1fcbea2a0f2c (drop_namespace_related_objects) has an intentional no-op downgrade
# because removing namespace tables is irreversible.  We stop there.
DOWNGRADE_TARGET = "1fcbea2a0f2c"

migration_engine = make_migration_engine("mergin_migration_test")
migration_app = make_migration_app(
    model_modules=[
        "mergin.auth.models",
        "mergin.stats.models",
        "mergin.sync.models",
    ]
)


def test_migration_lifecycle(migration_app, migration_engine):
    """Exercise the full migration chain: empty DB → head (one step at a time) → schema check → partial downgrade."""
    run_migration_lifecycle(
        migration_engine,
        MIGRATIONS_DIR,
        ordered_revisions(MIGRATIONS_DIR),
        db.metadata,
        DOWNGRADE_TARGET,
    )
