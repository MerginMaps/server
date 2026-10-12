# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
import tempfile


def isolate_xdist_worker():
    """Give each pytest-xdist worker its own database and temporary directories.

    Must run before app configuration is imported as it is read from env variables,
    this conftest is loaded right after test env file and before any tests modules.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if not worker:
        return

    db_name = f"{os.environ.get('DB_DATABASE', 'postgres')}_{worker}"
    os.environ["DB_DATABASE"] = db_name
    tmp_dir = tempfile.gettempdir()
    worker_tmp_dir = os.path.join(tmp_dir, db_name)
    os.makedirs(worker_tmp_dir, exist_ok=True)
    for key, value in list(os.environ.items()):
        if value == tmp_dir or value.startswith(tmp_dir + os.sep):
            os.environ[key] = worker_tmp_dir + value[len(tmp_dir) :]
    os.environ["TMPDIR"] = worker_tmp_dir
    tempfile.tempdir = None


isolate_xdist_worker()
