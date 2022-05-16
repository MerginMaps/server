# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import os
import hashlib
import re
import secrets
from threading import Timer
from uuid import UUID

from gevent import sleep


def generate_checksum(file, chunk_size=4096):
    """
    Generate checksum for file from chunks.

    :param file: file to calculate checksum
    :param chunk_size: size of chunk
    :return: sha1 checksum
    """
    checksum = hashlib.sha1()
    with open(file, 'rb') as f:
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
        with open(self.lockfile, 'a'):
            os.utime(self.lockfile, None)
        if self.running:
            self.timer = Timer(self.interval, self.touch_lockfile)
            self.timer.start()


def resolve_tags(files):
    def _is_qgis(filename):
        _, ext = os.path.splitext(filename)
        return ext in ['.qgs', '.qgz']

    tags = []
    qgis_count = 0
    for f in files:
        if _is_qgis(f['path']):
            qgis_count += 1
    #TODO add some rules for intput validity and mappin validity
    if qgis_count == 1:
        tags.extend(['valid_qgis', 'input_use'])
    return tags


def int_version(version):
    """ Convert v<n> format of version to integer representation. """
    return int(version.lstrip('v')) if re.match(r'v\d', version) else None


def is_versioned_file(file):
    """ Check if file is compatible with geodiff lib and hence suitable for versioning. """
    diff_extensions = ['.gpkg', '.sqlite']
    f_extension = os.path.splitext(file)[1]
    return f_extension in diff_extensions


def is_file_name_blacklisted(path, blacklist):
    blacklisted_dirs = get_blacklisted_dirs(blacklist)
    blacklisted_files = get_blacklisted_files(blacklist)
    if blacklisted_dirs:
        regexp_dirs = re.compile(r'({})'.format('|'.join(".*" + re.escape(x) + ".*" for x in blacklisted_dirs)))
        if regexp_dirs.search(os.path.dirname(path)):
            return True
    if blacklisted_files:
        regexp_files = re.compile(r'({})'.format('|'.join(".*" + re.escape(x) + ".*" for x in blacklisted_files)))
        if regexp_files.search(os.path.basename(path)):
            return True

    return False


def get_blacklisted_dirs(blacklist):
    return [p.replace("/", "") for p in blacklist if p.endswith("/")]


def get_blacklisted_files(blacklist):
    return [p for p in blacklist if not p.endswith("/")]


def get_user_agent(request):
    """ Return user agent from request headers

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
    """ Returns request's IP address based on X_FORWARDED_FOR header
    from proxy webserver (which should always be the case)
    """
    forwarded_ips = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'untrackable'))
    # seems like we get list of IP addresses from AWS infra (beginning with external IP address of client, followed by some internal IP)
    ip = forwarded_ips.split(",")[0]
    return ip


def generate_location():
    """ Return random location where project is saved on disk

    Example:
        >>> generate_location()
        '1c/624c6af4d6d2710bbfe1c128e8ca267b'
    """
    return os.path.join(secrets.token_hex(1), secrets.token_hex(16))


def is_valid_uuid(uuid):
    """ Check object can be parse as valid UUID """
    try:
        UUID(uuid)
        return True
    except (ValueError, AttributeError):
        return False
