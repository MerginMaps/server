# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import logging
import shutil
import os
import time
from datetime import datetime, timedelta
from flask import current_app

from .models import Project
from .storages.disk import move_to_tmp
from .config import Configuration
from ..celery import celery
from .. import db


@celery.task
def remove_temp_files():
    """Remove old temp folders in mergin temp directory.
    This is clean up for storages.disk.move_to_tmp() function.
    """
    for dir in os.listdir(current_app.config["TEMP_DIR"]):
        # ignore folder with apple notifications receipts which we want (temporarily) to maintain
        if dir == "notifications":
            continue
        path = os.path.join(current_app.config["TEMP_DIR"], dir)
        if datetime.fromtimestamp(
            os.path.getmtime(path)
        ) < datetime.utcnow() - timedelta(days=current_app.config["TEMP_EXPIRATION"]):
            try:
                shutil.rmtree(path)
            except OSError as e:
                print(f"Unable to remove {path}: {str(e)}")


@celery.task
def remove_projects_backups():
    """Permanently remove deleted projects. All data is lost, and project could not be restored anymore"""
    db.session.info = {"msg": "remove_projects_backups"}
    start = time.time()
    while True:
        if time.time() - start > 3 * 3600:
            logging.warning("Exiting remove_projects_backups as it took to long")
            break

        # process backlog
        projects = (
            Project.query.filter(
                Project.removed_at
                < datetime.utcnow()
                - timedelta(days=current_app.config["DELETED_PROJECT_EXPIRATION"])
            )
            .filter(Project.storage_params.isnot(None))
            .order_by(Project.removed_at.asc())
            .limit(100)
            .all()
        )

        if not len(projects):
            break

        for p in projects:
            p.delete()


@celery.task
def optimize_storage(project_id):
    """Optimize disk storage for project.

    Clean up for recently updated versioned files. Removes expired file versions.
    It applies only on files that can be recreated when needed.
    """
    db.session.info = {"msg": "optimize_storage"}
    project = (
        Project.query.filter_by(id=project_id)
        .filter(Project.storage_params.isnot(None))
        .first()
    )
    if not project:
        return

    for f in project.files:
        f_history = project.file_history(f["path"], "v1", project.latest_version)
        if not f_history:
            continue

        for item in f_history.values():
            # no diffs, it is a basefile for geodiff
            if item["diff"] is None:
                continue

            # skip the latest file version (high chance of being used)
            if item["location"] == f["location"]:
                continue

            abs_path = os.path.join(project.storage.project_dir, item["location"])
            # already removed
            if not os.path.exists(abs_path):
                continue

            age = time.time() - os.path.getmtime(abs_path)
            if age > Configuration.FILE_EXPIRATION:
                move_to_tmp(abs_path)
