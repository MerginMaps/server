# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial


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
