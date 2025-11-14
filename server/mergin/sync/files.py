# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import datetime
from enum import Enum
import os
from dataclasses import dataclass
from typing import Optional, List
import uuid
from flask import current_app
from marshmallow import ValidationError, fields, EXCLUDE, post_dump, validates_schema
from pathvalidate import sanitize_filename

from .utils import (
    is_file_name_blacklisted,
    is_supported_extension,
    is_valid_path,
    is_versioned_file,
    has_trailing_space,
)
from ..app import DateTimeWithZ, ma


class PushChangeType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UPDATE_DIFF = "update_diff"

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]


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
    """Base class for every file object, either intended to upload or already existing in project"""

    path: str
    checksum: str
    size: int

    def is_valid_gpkg(self):
        """Check if diff file is valid"""
        return self.size != 0


@dataclass
class ProjectDiffFile(File):
    """Metadata for geodiff diff file (aka. changeset) associated with geopackage"""

    # location where file is actually stored
    location: str


@dataclass
class ProjectFile(File):
    """Project file metadata including metadata for diff file and location where it is stored"""

    # metadata for gpkg diff file
    diff: Optional[ProjectDiffFile]
    # deprecated attribute kept for public API compatibility
    mtime: Optional[datetime.datetime]
    # location where file is actually stored
    location: str


@dataclass
class ProjectFileChange(ProjectFile):
    """Metadata of changed file in project version.

    This item is saved into database into file_history.
    """

    change: PushChangeType


def files_changes_from_upload(
    changes: dict, location_dir: str
) -> List["ProjectFileChange"]:
    """Create a list of version file changes from upload changes dictionary used by public API.

    It flattens changes dict and adds change type to each item. Also generates location for each file.
    """
    secure_filenames = []
    version_changes = []
    for key in ("added", "updated", "removed"):
        for item in changes.get(key, []):
            location = os.path.join(location_dir, mergin_secure_filename(item["path"]))
            diff = None

            # make sure we have unique location for each file
            if location in secure_filenames:
                filename, file_extension = os.path.splitext(location)
                location = filename + f".{str(uuid.uuid4())}" + file_extension

            secure_filenames.append(location)

            if key == "removed":
                change = PushChangeType.DELETE
                location = None
            elif key == "added":
                change = PushChangeType.CREATE
            else:
                change = PushChangeType.UPDATE
                if item.get("diff"):
                    change = PushChangeType.UPDATE_DIFF
                    diff_location = os.path.join(
                        location_dir, mergin_secure_filename(item["diff"]["path"])
                    )
                    if diff_location in secure_filenames:
                        filename, file_extension = os.path.splitext(diff_location)
                        diff_location = (
                            filename + f".{str(uuid.uuid4())}" + file_extension
                        )

                    secure_filenames.append(diff_location)
                    diff = ProjectDiffFile(
                        path=item["diff"]["path"],
                        checksum=item["diff"]["checksum"],
                        size=item["diff"]["size"],
                        location=diff_location,
                    )

            file_change = ProjectFileChange(
                path=item["path"],
                checksum=item["checksum"],
                size=item["size"],
                mtime=None,
                change=change,
                location=location,
                diff=diff,
            )
            version_changes.append(file_change)

    return version_changes


class FileSchema(ma.Schema):
    path = fields.String()
    size = fields.Integer()
    checksum = fields.String()

    class Meta:
        unknown = EXCLUDE


class UploadFileSchema(FileSchema):
    chunks = fields.List(fields.String(), load_default=[])
    diff = fields.Nested(FileSchema(), many=False, load_default=None)


class ChangesSchema(ma.Schema):
    """Schema for upload changes"""

    added = fields.List(
        fields.Nested(UploadFileSchema()), load_default=[], dump_default=[]
    )
    updated = fields.List(
        fields.Nested(UploadFileSchema()), load_default=[], dump_default=[]
    )
    removed = fields.List(
        fields.Nested(UploadFileSchema()), load_default=[], dump_default=[]
    )

    class Meta:
        unknown = EXCLUDE

    @post_dump
    def remove_blacklisted_files(self, data, **kwargs):
        """Files which are blacklisted are not allowed to be uploaded and are simple ignored."""
        for key in ("added", "updated", "removed"):
            data[key] = [
                f
                for f in data[key]
                if not is_file_name_blacklisted(
                    f["path"], current_app.config["BLACKLIST"]
                )
            ]
        return data

    @validates_schema
    def validate(self, data, **kwargs):
        """Basic consistency validations for upload metadata"""
        changes_files = [
            f["path"] for f in data["added"] + data["updated"] + data["removed"]
        ]

        if len(changes_files) == 0:
            raise ValidationError("No changes")

        # changes' files must be unique
        if len(set(changes_files)) != len(changes_files):
            raise ValidationError("Not unique changes")

        # check if all files are valid
        for file in data["added"] + data["updated"]:
            file_path = file["path"]
            if is_versioned_file(file_path) and file["size"] == 0:
                raise ValidationError("File is not valid")

            if not is_valid_path(file_path):
                raise ValidationError(
                    f"Unsupported file name detected: {file_path}. Please remove the invalid characters."
                )

            if not is_supported_extension(file_path):
                raise ValidationError(
                    f"Unsupported file type detected: {file_path}. "
                    f"Please remove the file or try compressing it into a ZIP file before uploading.",
                )
        # new checks must restrict only new files not to block existing projects
        for file in data["added"]:
            file_path = file["path"]
            if has_trailing_space(file_path):
                raise ValidationError(
                    f"Folder name contains a trailing space. Please remove the space in: {file_path}"
                )


class ProjectFileSchema(FileSchema):
    mtime = DateTimeWithZ()
    diff = fields.Nested(FileSchema())

    @post_dump
    def patch_field(self, data, **kwargs):
        # drop 'diff' key entirely if empty or None as clients would expect
        if not data.get("diff"):
            data.pop("diff")
        return data
