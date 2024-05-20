# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import math
import os
import hashlib
import re
import secrets
from threading import Timer
from uuid import UUID
from connexion import NoContent
from pathvalidate import sanitize_filename
from shapely import wkb
from shapely.errors import WKBReadingError
from gevent import sleep
from flask import Request
from typing import Optional


def generate_checksum(file, chunk_size=4096):
    """
    Generate checksum for file from chunks.

    :param file: file to calculate checksum
    :param chunk_size: size of chunk
    :return: sha1 checksum
    """
    checksum = hashlib.sha1()
    with open(file, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            sleep(0)  # to unblock greenlet
            if not chunk:
                return checksum.hexdigest()
            checksum.update(chunk)


class Toucher:
    """
    Helper class to periodically update modification time of file during
    execution of longer lasting task.

    Example of usage:
    -----------------
    with Toucher(file, interval):
        do_something_slow

    """

    def __init__(self, lockfile, interval):
        self.lockfile = lockfile
        self.interval = interval
        self.running = False
        self.timer = None

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, tb):  # pylint: disable=W0612,W0622
        self.release()

    def release(self):
        self.running = False
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def acquire(self):
        self.running = True
        self.touch_lockfile()

    def touch_lockfile(self):
        # do an NFS ACCESS procedure request to clear the attribute cache (for various pods to actually see the file)
        # https://docs.aws.amazon.com/efs/latest/ug/troubleshooting-efs-general.html#custom-nfs-settings-write-delays
        os.access(self.lockfile, os.W_OK)
        with open(self.lockfile, "a"):
            os.utime(self.lockfile, None)
        if self.running:
            self.timer = Timer(self.interval, self.touch_lockfile)
            self.timer.start()


def is_qgis(path: str) -> bool:
    """
    Check if file is a QGIS project file.
    """
    _, ext = os.path.splitext(path)
    return ext.lower() in [".qgs", ".qgz"]


def resolve_tags(files):
    tags = []
    qgis_count = 0
    for f in files:
        if is_qgis(f["path"]):
            qgis_count += 1
    # TODO add some rules for intput validity and mappin validity
    if qgis_count == 1:
        tags.extend(["valid_qgis", "input_use"])
    return tags


def int_version(version):
    """Convert v<n> format of version to integer representation."""
    return int(version.lstrip("v")) if re.match(r"v\d", version) else None


def is_versioned_file(file):
    """Check if file is compatible with geodiff lib and hence suitable for versioning."""
    diff_extensions = [".gpkg", ".sqlite"]
    f_extension = os.path.splitext(file)[1]
    return f_extension.lower() in diff_extensions


def is_file_name_blacklisted(path, blacklist):
    blacklisted_dirs = get_blacklisted_dirs(blacklist)
    blacklisted_files = get_blacklisted_files(blacklist)
    if blacklisted_dirs:
        regexp_dirs = re.compile(
            r"({})".format(
                "|".join(".*" + re.escape(x) + ".*" for x in blacklisted_dirs)
            )
        )
        if regexp_dirs.search(os.path.dirname(path)):
            return True
    if blacklisted_files:
        regexp_files = re.compile(
            r"({})".format(
                "|".join(".*" + re.escape(x) + ".*" for x in blacklisted_files)
            )
        )
        if regexp_files.search(os.path.basename(path)):
            return True

    return False


def get_blacklisted_dirs(blacklist):
    return [p.replace("/", "") for p in blacklist if p.endswith("/")]


def get_blacklisted_files(blacklist):
    return [p for p in blacklist if not p.endswith("/")]


def get_user_agent(request):
    """Return user agent from request headers

    In case of browser client a parsed version from werkzeug utils is returned else raw value of header.
    """
    if request.user_agent.browser and request.user_agent.platform:
        client = request.user_agent.browser.capitalize()
        version = request.user_agent.version
        system = request.user_agent.platform.capitalize()
        return f"{client}/{version} ({system})"
    else:
        return request.user_agent.string


def get_ip(request):
    """Returns request's IP address based on X_FORWARDED_FOR header
    from proxy webserver (which should always be the case)
    """
    forwarded_ips = request.environ.get(
        "HTTP_X_FORWARDED_FOR", request.environ.get("REMOTE_ADDR", "untrackable")
    )
    # seems like we get list of IP addresses from AWS infra (beginning with external IP address of client, followed by some internal IP)
    ip = forwarded_ips.split(",")[0]
    return ip


def generate_location():
    """Return random location where project is saved on disk

    Example:
        >>> generate_location()
        '1c/624c6af4d6d2710bbfe1c128e8ca267b'
    """
    return os.path.join(secrets.token_hex(1), secrets.token_hex(16))


def is_valid_uuid(uuid):
    """Check object can be parse as valid UUID"""
    try:
        UUID(uuid)
        return True
    except (ValueError, AttributeError):
        return False


# inspired by C++ implementation https://github.com/lutraconsulting/geodiff/blob/master/geodiff/src/drivers/sqliteutils.cpp
# in geodiff lib (MIT licence)
def parse_gpkgb_header_size(gpkg_wkb):
    """Parse header of geopackage wkb and return its size"""
    # some constants
    no_envelope_header_size = 8
    flag_byte_pos = 3
    envelope_size_mask = 14

    try:
        flag_byte = gpkg_wkb[flag_byte_pos]
    except IndexError:
        return -1  # probably some invalid input
    envelope_byte = (flag_byte & envelope_size_mask) >> 1
    envelope_size = 0

    if envelope_byte == 1:
        envelope_size = 32
    elif envelope_byte == 2:
        envelope_size = 48
    elif envelope_byte == 3:
        envelope_size = 48
    elif envelope_byte == 4:
        envelope_size = 64

    return no_envelope_header_size + envelope_size


def gpkg_wkb_to_wkt(gpkg_wkb):
    """Convert WKB (with gpkg header) to WKT"""
    wkb_header_length = parse_gpkgb_header_size(gpkg_wkb)
    wkb_geom = gpkg_wkb[wkb_header_length:]
    try:
        wkt = wkb.loads(wkb_geom).wkt
    except WKBReadingError:
        wkt = None
    return wkt


def get_byte_string(size_bytes):
    """Return string of size_bytes in string

    :param size_bytes: size_bytes to string.
    :type size_bytes: int

    :return: size bytes in string.
    :rtype: str
    """

    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, i)
    size = round(size_bytes / power, 2)
    return "%s %s" % (size, size_name[i])


def convert_byte(size_bytes, unit):
    """Convert byte into other unit

    :param size_bytes: size_bytes to target.
    :type size_bytes: int

    :param unit: target unit .
    :type unit: str

    :return: size in target unit.
    :rtype: float
    """

    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = 0
    try:
        i = units.index(unit.upper())
    except ValueError:
        pass
    if i > 0:
        power = math.pow(1024, i)
        size_bytes = round(size_bytes / power, 2)
    return size_bytes


def is_name_allowed(string):
    """Check if string is just has whitelisted character

    :param string: string to be checked.
    :type string: str

    :return: boolean of has just whitelisted character
    :rtype: bool
    """
    return (
        re.match(
            r".*[\@\#\$\%\^\&\*\(\)\{\}\[\]\?\'\"`,;\:\+\=\~\\\/\|\<\>].*|^[\s^\.].*$|^CON$|^PRN$|^AUX$|^NUL$|^COM\d$|^LPT\d|^support$|^helpdesk$|^merginmaps$|^lutraconsulting$|^mergin$|^lutra$|^input$|^admin$|^sales$|^$",
            string,
        )
        is None
    )


def mergin_secure_filename(filename):
    """Change filename to be secured filename

    :param filename: string to be checked.
    :type filename: str

    :return: secured filename
    :rtype: str
    """
    filename = os.path.normpath(filename)
    return os.path.join(
        *[
            sanitize_filename(path, replacement_text="_")
            for path in filename.split(os.sep)
        ]
    )


def get_path_from_files(files, path, is_diff=False):
    """Get path from files between getting sanitized or mergin_secure_filename

    :param files: list of files
    :type files: list

    :param path: path that will be checked
    :type path: str

    :return: secured filename
    :rtype: str
    """
    for file in files:
        if file["path"] == path:
            if is_diff:
                return (
                    file["diff"]["sanitized_path"]
                    if "sanitized_path" in file
                    else file["diff"]["path"]
                )
            else:
                return (
                    file["sanitized_path"] if "sanitized_path" in file else file["path"]
                )
    return mergin_secure_filename(path)


def workspace_names(workspaces):
    """Helper to extract only names from list of workspaces"""
    return list(map(lambda x: x.name, workspaces))


def workspace_ids(workspaces):
    """Helper to extract only ids from list of workspaces"""
    return list(map(lambda x: x.id, workspaces))


def get_project_path(project):
    """Create path for the project."""
    project_path = project.workspace.name + "/" + project.name
    return project_path


def split_project_path(project_path):
    """Extract workspace and project names out of path."""
    workspace_name, project_name = project_path.split("/")
    return workspace_name, project_name


def is_valid_gpkg(file_meta):
    """Check if diff file is valid"""
    return file_meta["size"] != 0


def clean_upload(transaction_id):
    """Clean upload infrastructure

    Uploaded files and table records are removed, and another upload can be started.

    :param transaction_id: Transaction id.
    :type transaction_id: Str

    :rtype: None
    """
    from mergin.sync.permissions import get_upload
    from mergin.sync.storages.disk import move_to_tmp
    from .. import db

    upload, upload_dir = get_upload(transaction_id)
    db.session.delete(upload)
    db.session.commit()
    move_to_tmp(upload_dir, transaction_id)
    return NoContent, 200


def get_device_id(request: Request) -> Optional[str]:
    """Get device uuid from http header X-Device-Id"""
    return request.headers.get("X-Device-Id")
