# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import logging
import math
import shutil
import os
import time
from datetime import datetime, timedelta, timezone
import uuid
from zipfile import ZIP_DEFLATED, ZipFile
from flask import current_app
from pygeodiff import GeoDiffLibError
from pygeodiff.geodifflib import GeoDiffLibConflictError

from .models import FileDiff, Project, ProjectVersion, FileHistory
from .storages.disk import move_to_tmp
from .config import Configuration
from .utils import LOG_BASE, generate_checksum, get_merged_versions
from ..celery import celery
from ..app import db


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
        f_history = FileHistory.changes(project.id, f.path, 1, project.latest_version)
        if not f_history:
            continue

        for item in f_history:
            # no diffs, it is a basefile for geodiff
            if not item.diff_file:
                continue

            # skip the latest file version (high chance of being used)
            if item.location == f.location:
                continue

            # already removed
            if not os.path.exists(item.abs_path):
                continue

            age = time.time() - os.path.getmtime(item.abs_path)
            if age > Configuration.FILE_EXPIRATION:
                move_to_tmp(item.abs_path)


@celery.task
def create_project_version_zip(version_id: int):
    """Create zip file for project version."""
    db.session.info = {"msg": "create_project_version_zip"}
    project_version = ProjectVersion.query.get(version_id)
    if not project_version:
        return

    zip_path = project_version.zip_path + ".partial"
    if os.path.exists(zip_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(zip_path), tz=timezone.utc)
        expiration_time = datetime.now(timezone.utc) - timedelta(
            seconds=current_app.config["PARTIAL_ZIP_EXPIRATION"]
        )
        if mtime > expiration_time:
            # partial zip is recent -> another job is likely running
            return
        else:
            # partial zip is too old -> remove and creating new one
            os.remove(zip_path)

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    try:
        with ZipFile(
            zip_path,
            "w",
            compression=ZIP_DEFLATED,
            compresslevel=1,
        ) as archive:
            for f in project_version.files:
                project_version.project.storage.restore_versioned_file(
                    f.path, project_version.name
                )
                archive.write(
                    project_version.project.storage.file_path(f.location), f.path
                )
        # move zip file to final location
        os.rename(zip_path, project_version.zip_path)
    finally:
        # remove partial zip file if exists
        if os.path.exists(zip_path):
            os.remove(zip_path)


@celery.task
def remove_projects_archives():
    """Remove created zip files for project versions if they were not accessed for certain time"""
    for file in os.listdir(current_app.config["PROJECTS_ARCHIVES_DIR"]):
        path = os.path.join(current_app.config["PROJECTS_ARCHIVES_DIR"], file)
        if datetime.fromtimestamp(
            os.path.getatime(path), tz=timezone.utc
        ) < datetime.now(timezone.utc) - timedelta(
            days=current_app.config["PROJECTS_ARCHIVES_EXPIRATION"]
        ):
            try:
                os.remove(path)
            except OSError as e:
                logging.error(f"Unable to remove {path}: {str(e)}")


@celery.task
def create_diff_checkpoint(file_id: int, start: int, end: int):
    """Create a diff file checkpoint (aka. merged diff).
    Find all smaller diffs which are needed to create the final diff file and merge them.
    In case of missing some lower rank checkpoint, use individual diffs instead.
    """
    db.session.info = {"msg": "create_diff_checkpoint"}
    diff_range = end - start + 1

    # invalid request as there would not be a checkpoint with this range
    if end % LOG_BASE or diff_range % LOG_BASE:
        return

    rank = math.log(diff_range) / math.log(LOG_BASE)
    if not rank.is_integer():
        return

    # checkpoint already exists
    file_diff = FileDiff.query.filter_by(
        file_path_id=file_id, version=end, rank=rank
    ).first()
    if file_diff and os.path.exists(file_diff.abs_path):
        return

    basefile = FileHistory.get_basefile(file_id, end)
    if not basefile:
        logging.error(f"Unable to find basefile for file {file_id}")
        return

    if basefile.project_version_name > start:
        logging.error(
            f"Basefile version {basefile.project_version_name} is higher than start version {start} - broken history"
        )
        return

    diffs_paths = []
    file_diffs = (
        FileDiff.query.filter(
            FileDiff.basefile_id == basefile.id,
            FileDiff.version >= start,
            FileDiff.version <= end,
        )
        .order_by(FileDiff.rank, FileDiff.version)
        .all()
    )

    # we apply latest change (if any) on previous version
    end_diff = next((d for d in file_diffs if d.version == end and d.rank == 0), None)
    # let's confirm we have all intermediate diffs needed, if not, we need to use individual diffs instead
    for merged_diff in get_merged_versions(start, end - 1):
        # basefile is a start of the diff chain
        if merged_diff.start <= basefile.project_version_name:
            continue

        # find diff in table and on disk
        diff = next(
            (
                d
                for d in file_diffs
                if d.version == merged_diff.end and d.rank == merged_diff.rank
            ),
            None,
        )
        if diff and os.path.exists(diff.abs_path):
            diffs_paths.append(diff.abs_path)
        else:
            individual_diffs = [
                d.abs_path
                for d in file_diffs
                if d.rank == 0
                and d.version >= merged_diff.start
                and d.version <= merged_diff.end
            ]
            if individual_diffs:
                diffs_paths.extend(individual_diffs)
            else:
                logging.error(
                    f"Unable to find diffs for {merged_diff} for file {file_id}"
                )
                return

    if end_diff:
        diffs_paths.append(end_diff.abs_path)

    if not diffs_paths:
        logging.warning(f"No diffs for next checkpoint for file {file_id}")
        return

    project: Project = basefile.file.project
    checkpoint_path = f"diff-{uuid.uuid4()}"
    os.makedirs(project.storage.diffs_dir, exist_ok=True)
    checkpoint_file = os.path.join(project.storage.diffs_dir, checkpoint_path)
    try:
        project.storage.geodiff.concat_changes(diffs_paths, checkpoint_file)
    except (GeoDiffLibError, GeoDiffLibConflictError):
        logging.error(f"Geodiff: Failed to merge diffs for file {file_id}")
        return

    checkpoint = FileDiff(
        basefile=basefile,
        path=checkpoint_path,
        size=os.path.getsize(checkpoint_file),
        checksum=generate_checksum(checkpoint_file),
        rank=rank,
        version=end,
    )
    db.session.add(checkpoint)
    db.session.commit()
