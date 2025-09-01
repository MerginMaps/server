# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from flask import current_app, abort
from sqlalchemy import event
from sqlalchemy.sql import text

from ..app import db
from .models import ProjectVersion
from .public_api_controller import project_version_created
from .tasks import create_diff_checkpoint
from .utils import get_cached_levels


def check(session):
    if os.path.isfile(current_app.config["MAINTENANCE_FILE"]):
        abort(503, "Service unavailable due to maintenance, please try later")


def create_checkpoints(project_version: ProjectVersion):
    """
    Create version checkpoints related to new project version
    """
    # for initial versions there is nothing to do
    if project_version.name in (0, 1):
        return

    cache_levels = get_cached_levels(project_version.name)
    if not cache_levels:
        return

    # get all diff-modified gpkg files
    query = text(
        """
        WITH gpkg_files AS (
            SELECT id 
            FROM project_file_path 
            WHERE 
                project_id = :project_id
                AND lower(path) LIKE '%.gpkg'
        ),
        latest_updates AS (
            SELECT DISTINCT
                gf.id,
                max(fh.project_version_name) AS latest_version
                FROM gpkg_files gf
                INNER JOIN file_history fh ON fh.file_path_id = gf.id
                GROUP BY gf.id
        )        
        SELECT 
            lu.id 
        FROM latest_updates lu
        LEFT OUTER JOIN file_history fh ON lu.id = fh.file_path_id AND lu.latest_version = fh.project_version_name
        WHERE fh.change = 'update_diff';
    """
    )
    result = db.session.execute(
        query, {"project_id": project_version.project_id}
    ).fetchall()

    # create batch of caching jobs
    for row in result:
        for level in cache_levels:
            create_diff_checkpoint.delay(row.id, level.start, level.end)


def register_events():
    event.listen(db.session, "before_commit", check)
    project_version_created.connect(create_checkpoints)


def remove_events():
    event.remove(db.session, "before_commit", check)
    project_version_created.disconnect(create_checkpoints)
