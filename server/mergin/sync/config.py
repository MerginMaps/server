# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from tempfile import gettempdir
from decouple import config, Csv

config_dir = os.path.abspath(os.path.dirname(__file__))


class Configuration(object):
    LOCAL_PROJECTS = config(
        "LOCAL_PROJECTS",
        default=os.path.join(config_dir, os.pardir, os.pardir, os.pardir, "projects"),
    )
    PROJECTS_ARCHIVES_DIR = config(
        "PROJECTS_ARCHIVES_DIR",
        default=os.path.join(LOCAL_PROJECTS, "projects_archives"),
    )
    PROJECTS_ARCHIVES_EXPIRATION = config(
        "PROJECTS_ARCHIVES_EXPIRATION", cast=int, default=7
    )
    # locking file when backups are created
    MAINTENANCE_FILE = config(
        "MAINTENANCE_FILE", default=os.path.join(LOCAL_PROJECTS, "MAINTENANCE")
    )
    LOCKFILE_EXPIRATION = config(
        "LOCKFILE_EXPIRATION", default=300, cast=int
    )  # in seconds
    MAX_CHUNK_SIZE = config(
        "MAX_CHUNK_SIZE", default=10 * 1024 * 1024, cast=int
    )  # in bytes
    # use nginx (in front of gunicorn) to serve files (https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/)
    USE_X_ACCEL = config("USE_X_ACCEL", default=False, cast=bool)
    # for clean up of old files where diffs were applied, in seconds
    FILE_EXPIRATION = config("FILE_EXPIRATION", default=48 * 3600, cast=int)
    BLACKLIST = config(
        "BLACKLIST", default=".mergin/, .DS_Store, .directory", cast=Csv()
    )
    # max total files size for archive download
    MAX_DOWNLOAD_ARCHIVE_SIZE = config(
        "MAX_DOWNLOAD_ARCHIVE_SIZE", default=1024 * 1024 * 1024, cast=int
    )
    PROJECT_ACCESS_REQUEST = config(
        "PROJECT_ACCESS_REQUEST", default=7 * 24 * 3600, cast=int
    )
    TEMP_EXPIRATION = config(
        "TEMP_EXPIRATION", default=7, cast=int
    )  # time in days after files are permanently deleted
    # lifetime of deleted project, expired project are removed permanently without restore possibility, in days
    DELETED_PROJECT_EXPIRATION = config(
        "DELETED_PROJECT_EXPIRATION", default=7, cast=int
    )
    # trash dir for temp files being cleaned regularly
    TEMP_DIR = config("TEMP_DIR", default=gettempdir())
    # working directory for geodiff actions - should be a fast local storage
    GEODIFF_WORKING_DIR = config(
        "GEODIFF_WORKING_DIR",
        default=os.path.join(LOCAL_PROJECTS, "geodiff_tmp"),
    )
