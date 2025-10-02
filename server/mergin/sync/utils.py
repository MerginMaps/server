# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import logging
import math
import os
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from threading import Timer
from uuid import UUID
from shapely import wkb
from shapely.errors import ShapelyError
from gevent import sleep
from flask import Request
from typing import Optional, Tuple
from sqlalchemy import text
from pathvalidate import (
    validate_filename,
    ValidationError,
    is_valid_filepath,
    is_valid_filename,
)
import magic
from flask import current_app


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

        sleep(0)  # to unblock greenlet
        if self.running:
            self.timer = Timer(self.interval, self.touch_lockfile)
            self.timer.start()


def is_qgis(path: str) -> bool:
    """
    Check if file is a QGIS project file.
    """
    _, ext = os.path.splitext(path)
    return ext.lower() in [".qgs", ".qgz"]


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
    except ShapelyError:
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


def is_reserved_word(name: str) -> str | None:
    """Check if name is reserved in system"""
    reserved = r"^support$|^helpdesk$|^merginmaps$|^lutraconsulting$|^mergin$|^lutra$|^input$|^admin$|^sales$"
    if re.match(reserved, name) is not None:
        return "The provided value is invalid."
    return None


def has_valid_characters(name: str) -> str | None:
    """Check if name contains only valid characters"""
    if re.match(r"^[\w\s\-\.]+$", name) is None:
        return "Please use only alphanumeric or the following -_. characters."
    return None


def has_valid_first_character(name: str) -> str | None:
    """Check if name contains only valid characters in first position"""
    if re.match(r"^[\s.].*$", name) is not None:
        return f"Value can not start with space or dot."
    return None


def check_filename(name: str) -> str | None:
    """Check if name contains only valid characters for filename"""
    error = None
    try:
        validate_filename(name)
    except ValidationError:
        error = "The provided value is invalid."
    return error


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


def get_device_id(request: Request) -> Optional[str]:
    """Get device uuid from http header X-Device-Id"""
    return request.headers.get("X-Device-Id")


def files_size():
    """Get total size of all files"""
    from mergin.app import db

    files_size = text(
        f"""
        WITH partials AS (
            WITH latest_files AS (
                SELECT distinct unnest(file_history_ids) AS file_id
                FROM latest_project_files pf
            )
            SELECT
                SUM(size)
            FROM file_history
            WHERE change = 'create'::push_change_type OR change = 'update'::push_change_type
            UNION
            SELECT
                SUM(size)
            FROM file_diff
            UNION
            SELECT
                SUM(size)
            FROM latest_files lf
            LEFT OUTER JOIN file_history fh ON fh.id = lf.file_id
            WHERE fh.change = 'update_diff'::push_change_type
        )
        SELECT COALESCE(SUM(sum), 0) FROM partials;
        """
    )
    return db.session.execute(files_size).scalar()


def is_valid_path(filepath: str) -> bool:
    """Check filepath and filename for invalid characters, absolute path or path traversal"""
    return (
        not len(re.split(r"\.[/\\]", filepath)) > 1  # ./ or .\
        and is_valid_filepath(filepath)  # invalid characters in filepath, absolute path
        and is_valid_filename(
            os.path.basename(filepath)
        )  # invalid characters in filename, reserved filenames
    )


def is_supported_extension(filepath) -> bool:
    """Check whether file's extension is supported."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext and ext not in FORBIDDEN_EXTENSIONS


FORBIDDEN_EXTENSIONS = {
    ".ade",
    ".adp",
    ".app",
    ".appcontent-ms",
    ".application",
    ".appref-ms",
    ".asp",
    ".aspx",
    ".asx",
    ".bas",
    ".bat",
    ".bgi",
    ".cab",
    ".cdxml",
    ".cer",
    ".chm",
    ".cmd",
    ".cnt",
    ".com",
    ".cpl",
    ".crt",
    ".csh",
    ".der",
    ".diagcab",
    ".dll",
    ".drv",
    ".exe",
    ".fxp",
    ".gadget",
    ".grp",
    ".hlp",
    ".hpj",
    ".hta",
    ".htc",
    ".htaccess",
    ".htpasswd",
    ".inf",
    ".ins",
    ".iso",
    ".isp",
    ".its",
    ".jar",
    ".jnlp",
    ".js",
    ".jse",
    ".jsp",
    ".ksh",
    ".lnk",
    ".mad",
    ".maf",
    ".mag",
    ".mam",
    ".maq",
    ".mar",
    ".mas",
    ".mat",
    ".mau",
    ".mav",
    ".maw",
    ".mcf",
    ".mda",
    ".mdb",
    ".mde",
    ".mdt",
    ".mdw",
    ".mdz",
    ".msc",
    ".mht",
    ".mhtml",
    ".msh",
    ".msh1",
    ".msh2",
    ".mshxml",
    ".msh1xml",
    ".msh2xml",
    ".msi",
    ".msp",
    ".mst",
    ".msu",
    ".ops",
    ".osd",
    ".pcd",
    ".pif",
    ".pl",
    ".plg",
    ".prf",
    ".prg",
    ".printerexport",
    ".ps1",
    ".ps1xml",
    ".ps2",
    ".ps2xml",
    ".psc1",
    ".psc2",
    ".psd1",
    ".psdm1",
    ".pssc",
    ".pst",
    ".py",
    ".pyc",
    ".pyo",
    ".pyw",
    ".pyz",
    ".pyzw",
    ".reg",
    ".scf",
    ".scr",
    ".sct",
    ".settingcontent-ms",
    ".sh",
    ".shb",
    ".shs",
    ".sys",
    ".theme",
    ".tmp",
    ".torrent",
    ".url",
    ".vb",
    ".vbe",
    ".vbp",
    ".vbs",
    ".vhd",
    ".vhdx",
    ".vsmacros",
    ".vsw",
    ".webpnp",
    ".website",
    ".ws",
    ".wsb",
    ".wsc",
    ".wsf",
    ".wsh",
    ".xbap",
    ".xll",
    ".xnk",
}

FORBIDDEN_MIME_TYPES = {
    "application/x-msdownload",
    "application/x-sh",
    "application/x-bat",
    "application/x-msdos-program",
    "application/x-dosexec",
    "application/x-csh",
    "application/x-perl",
    "application/javascript",
    "application/x-python-code",
    "application/x-ruby",
    "application/java-archive",
    "application/vnd.ms-cab-compressed",
    "application/x-ms-shortcut",
    "application/vnd.microsoft.portable-executable",
    "application/x-ms-installer",
    "application/x-ms-application",
    "application/x-ms-wim",
    "text/x-shellscript",
}


def is_supported_type(filepath) -> bool:
    """Check whether the file mimetype is supported."""
    mime_type = get_mimetype(filepath)
    return mime_type.startswith("image/") or mime_type not in FORBIDDEN_MIME_TYPES


def get_mimetype(filepath: str) -> str:
    """Identifies file types by checking their headers"""
    return magic.from_file(filepath, mime=True)


def get_x_accel_uri(*url_parts):
    """
    Constructs a URI for X-Accel redirection based on the provided URL parts. We are using /download in our nginx config for this purpose.
    Therefore, we need to adjust the path to start with "/download".

    If url_parts starts with LOCAL_PROJECTS path, adjust the path to start with "/download" and remove it from the beginning of the path.
    Args:
        *url_parts: parts of the path of the file to be served.
    Returns:
        str: A URI string starting with "/download", followed by the joined
             and adjusted path based on the provided URL parts.
    Example:
        Assuming `current_app.config["LOCAL_PROJECTS"]` is set to
        "/home":
        >>> get_x_accel_uri("/home", "example", "file.txt")
        '/download/example/file.txt'
    """
    download_accell_uri = "/download"
    if not url_parts:
        return download_accell_uri

    local_projects = current_app.config.get("LOCAL_PROJECTS")
    url = os.path.join(*url_parts)
    # if the path parts_join starts with local_projects, remove it
    if url.startswith(local_projects):
        url = os.path.relpath(url, local_projects)
    url = url.lstrip(os.path.sep)
    result = os.path.join(download_accell_uri, url)
    return result


def get_chunk_location(id: str):
    """
    Get file location for chunk on FS

    Splits the given identifier into two parts where the first two characters of the identifier are the small hash,
    and the remaining characters is a file identifier.
    """
    chunk_dir = current_app.config.get("UPLOAD_CHUNKS_DIR")
    small_hash = id[:2]
    file_name = id[2:]
    return os.path.join(chunk_dir, small_hash, file_name)


def remove_outdated_files(dir: str, time_delta: timedelta):
    """Remove all files within directory where last access time passed expiration date"""
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        if not os.path.isfile(path):
            continue

        if (
            datetime.fromtimestamp(os.path.getatime(path), tz=timezone.utc)
            < datetime.now(timezone.utc) - time_delta
        ):
            try:
                os.remove(path)
            except OSError as e:
                logging.error(f"Unable to remove {path}: {str(e)}")
