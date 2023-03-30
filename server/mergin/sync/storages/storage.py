# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from urllib.parse import quote
from flask import Response
from requests_toolbelt import MultipartEncoder
from gevent import sleep
import zipfly


class InvalidProject(Exception):
    pass


class FileNotFound(Exception):
    pass


class DataSyncError(Exception):
    pass


class InitializationError(Exception):
    pass


class StorageFile(object):
    def __init__(self, storage, file):
        self.storage = storage
        self.file = file
        self.fp = 0
        self._stream = None

    @property
    def len(self):
        if not hasattr(self, "_total_len"):
            self._total_len = self.storage.file_size(self.file)
        return self._total_len - self.fp

    def read(self, chunk_size):
        if not self._stream:
            self._preload = b""
            self._stream = self.storage.read_file(self.file, chunk_size)

        data = self._preload
        while len(data) < chunk_size:
            try:
                chunk = next(self._stream)
            except StopIteration:
                chunk = None
            if not chunk:
                self._preload = b""
                self.fp += len(data)
                return data
            data += chunk

        self._preload = data[chunk_size:]
        data = data[:chunk_size]
        self.fp += len(data)
        return data


class ProjectStorage:
    def __init__(self, project):
        self.project = project

    def read_file(self, path, block_size=4096):
        raise NotImplementedError

    def file_size(self, file):
        raise NotImplementedError

    def file_path(self, file):
        raise NotImplementedError

    def restore_versioned_file(self, file, version):
        raise NotImplementedError

    def download_files(self, files, files_format=None, version=None):
        """Download files
        :type files: list of dict
        """
        if version:
            for f in files:
                sleep(0)
                self.restore_versioned_file(f["path"], version)
        if files_format == "zip":
            paths = [
                {"fs": self.file_path(f["location"]), "n": f["path"]} for f in files
            ]
            z = zipfly.ZipFly(mode="w", paths=paths)
            response = Response(z.generator(), mimetype="application/zip")
            response.headers[
                "Content-Disposition"
            ] = "attachment; filename={}{}.zip".format(
                quote(self.project.name.encode("utf-8")),
                "-" + version if version else "",
            )
            return response
        files_dict = {}
        for f in files:
            path = f["path"]
            files_dict[path] = (path, StorageFile(self, f["location"]))
        encoder = MultipartEncoder(files_dict)

        def _generator():
            while True:
                data = encoder.read(4096)
                sleep(0)
                if data:
                    yield data
                else:
                    break

        return Response(_generator(), mimetype=encoder.content_type)
