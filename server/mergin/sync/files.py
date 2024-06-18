# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import datetime
import os
from dataclasses import dataclass
from typing import Optional, List
from marshmallow import fields, EXCLUDE, pre_load, post_load
from pathvalidate import sanitize_filename

from server.mergin import ma


def mergin_secure_filename(filename: str) -> str:
    """ Generate secure filename for given file """
    filename = os.path.normpath(filename)
    return os.path.join(
        *[
            sanitize_filename(path, replacement_text="_")
            for path in filename.split(os.sep)
        ]
    )


@dataclass
class FileMeta:
    """Base class for every file object"""
    path: str
    checksum: str
    size: int

    def is_valid_gpkg(self):
        """Check if diff file is valid"""
        return self.size != 0


@dataclass
class LocalFile(FileMeta):
    """File stored on server"""
    location: str


@dataclass
class ProjectFile(LocalFile):
    """Project file metadata including diff meta"""
    diff: Optional[LocalFile]
    mtime: Optional[datetime.datetime]  # deprecated attribute kept for public API compatibility


@dataclass
class UploadFile(FileMeta):
    """File to be uploaded with secure filename"""
    sanitized_path: str  # added by server


@dataclass
class UploadFileInfo(UploadFile):
    """File to be uploaded coming from client push process"""
    chunks: Optional[List[str]]  # determined by client
    diff: Optional[UploadFile]


@dataclass
class UploadChanges:
    added: List[UploadFileInfo]
    updated: List[UploadFileInfo]
    removed: List[UploadFileInfo]


class UploadFileSchema(ma.Schema):
    path = fields.String()
    checksum = fields.String()
    size = fields.Integer()
    sanitized_path = fields.String(load_default="", load_only=True)

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def pre_load(self, data, **kwargs):
        if not data.get("sanitized_path"):
            data["sanitized_path"] = mergin_secure_filename(data["path"])
        return data

    @post_load
    def create_obj(self, data, **kwargs):
        return UploadFile(**data)


class UploadFileInfoSchema(UploadFileSchema):
    chunks = fields.List(fields.String(), load_default=[])
    diff = fields.Nested(UploadFileSchema(), many=False, load_default=None)

    @post_load
    def create_obj(self, data, **kwargs):
        return UploadFileInfo(**data)


class UploadChangesSchema(ma.Schema):
    added = fields.List(fields.Nested(UploadFileInfoSchema()), load_default=[])
    updated = fields.List(fields.Nested(UploadFileInfoSchema()), load_default=[])
    removed = fields.List(fields.Nested(UploadFileInfoSchema()), load_default=[])

    @post_load
    def create_obj(self, data, **kwargs):
        return UploadChanges(**data)
