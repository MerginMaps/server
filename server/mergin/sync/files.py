# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import datetime
import os
from dataclasses import dataclass
from typing import Optional, List
from marshmallow import fields, EXCLUDE, pre_load, post_load, post_dump
from pathvalidate import sanitize_filename

from ..app import DateTimeWithZ, ma


def mergin_secure_filename(filename: str) -> str:
    """Generate secure filename for given file"""
    filename = os.path.normpath(filename)
    return os.path.join(
        *[
            sanitize_filename(path, replacement_text="_")
            for path in filename.split(os.sep)
        ]
    )


@dataclass
class File:
    """Base class for every file object"""

    path: str
    checksum: str
    size: int
    location: str

    def is_valid_gpkg(self):
        """Check if diff file is valid"""
        return self.size != 0


@dataclass
class ProjectFile(File):
    """Project file metadata including metadata for diff file"""

    # metadata for gpkg diff file
    diff: Optional[File]
    # deprecated attribute kept for public API compatibility
    mtime: Optional[datetime.datetime]


@dataclass
class UploadFile(File):
    """File to be uploaded coming from client push process"""

    # determined by client
    chunks: Optional[List[str]]
    diff: Optional[File]


@dataclass
class UploadChanges:
    added: List[UploadFile]
    updated: List[UploadFile]
    removed: List[UploadFile]


class FileSchema(ma.Schema):
    path = fields.String()
    size = fields.Integer()
    checksum = fields.String()
    location = fields.String(load_default="", load_only=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def create_obj(self, data, **kwargs):
        return File(**data)


class UploadFileSchema(FileSchema):
    chunks = fields.List(fields.String(), load_default=[])
    diff = fields.Nested(FileSchema(), many=False, load_default=None)

    @pre_load
    def pre_load(self, data, **kwargs):
        # add future location based on context version
        version = f"v{self.context.get('version')}"
        if not data.get("location"):
            data["location"] = os.path.join(
                version, mergin_secure_filename(data["path"])
            )
        if data.get("diff") and not data.get("diff").get("location"):
            data["diff"]["location"] = os.path.join(
                version, mergin_secure_filename(data["diff"]["path"])
            )
        return data

    @post_load
    def create_obj(self, data, **kwargs):
        return UploadFile(**data)


class ChangesSchema(ma.Schema):
    """Schema for upload changes"""

    added = fields.List(fields.Nested(UploadFileSchema()), load_default=[])
    updated = fields.List(fields.Nested(UploadFileSchema()), load_default=[])
    removed = fields.List(fields.Nested(UploadFileSchema()), load_default=[])

    class Meta:
        unknown = EXCLUDE

    @post_load
    def create_obj(self, data, **kwargs):
        return UploadChanges(**data)


class ProjectFileSchema(FileSchema):
    mtime = DateTimeWithZ()
    diff = fields.Nested(FileSchema())

    @post_dump
    def patch_field(self, data, **kwargs):
        # drop 'diff' key entirely if empty or None as clients would expect
        if not data.get("diff"):
            data.pop("diff")
        return data
