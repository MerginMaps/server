# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
import io
import time
import uuid
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List

from flask import current_app
from pygeodiff import GeoDiff, GeoDiffLibError
from pygeodiff.geodifflib import GeoDiffLibConflictError
from gevent import sleep
from .storage import ProjectStorage, FileNotFound, DataSyncError, InitializationError
from ... import db
from ..utils import (
    generate_checksum,
    is_versioned_file,
    mergin_secure_filename,
)


def save_to_file(stream, path, max_size=None):
    """Save readable object in file while yielding to gevent hub.

    :param stream: object implementing readable interface
    :param path: destination file path
    :param max_size: limit for file size
    """
    directory = os.path.abspath(os.path.dirname(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as output:
        writer = io.BufferedWriter(output, buffer_size=32768)
        size = 0
        while True:
            part = stream.read(4096)
            sleep(0)  # to unblock greenlet
            if part:
                size += len(part)
                if max_size and size > max_size:
                    raise IOError()
                writer.write(part)
            else:
                writer.flush()
                break


def copy_file(src, dest):
    """Custom implementation of copying file by chunk with yielding to gevent hub.

    see save_to_file

    :params src: abs path to file
    :type src: str, path-like object
    :params dest: abs path to destination file
    :type dest: str, path-like object
    """
    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    directory = os.path.abspath(os.path.dirname(dest))
    os.makedirs(directory, exist_ok=True)
    with open(src, "rb") as input:
        save_to_file(input, dest)


def copy_dir(src, dest):
    """Custom implementation of recursive copy of directory with yielding to gevent hub.

    :params src: abs path to dir
    :type src: str, path-like object
    :params dest: destination folder
    :type dest: str, path-like object
    """
    if not os.path.isdir(src):
        raise NotADirectoryError(src)
    for root, dirs, files in os.walk(src):
        for file in files:
            abs_path = os.path.abspath(os.path.join(root, file))
            rel_path = os.path.relpath(abs_path, start=src)
            copy_file(abs_path, os.path.join(dest, rel_path))


def move_to_tmp(src, dest=None):
    """Custom handling of file/directory removal by moving it to regularly cleaned tmp folder.
    This is mainly to avoid using standard tools which could cause blocking gevent hub for large files.

    :params src: abs path to file/directory
    :type src: str, path-like object
    :params dest: subdir in temp folder (e.g. transaction_id), defaults to None
    :type dest: str, path-like object
    :returns: path where file is moved to
    :rtype: str, path-like object
    """
    if not os.path.exists(src):
        return
    dest = dest if dest else str(uuid.uuid4())
    rel_path = os.path.relpath(
        src, start=current_app.config["LOCAL_PROJECTS"]
    )  # take relative path from parent of all project files
    temp_path = os.path.join(current_app.config["TEMP_DIR"], dest, rel_path)
    os.renames(src, temp_path)
    return temp_path


class DiskStorage(ProjectStorage):
    def __init__(self, project):
        super(DiskStorage, self).__init__(project)
        self.projects_dir = current_app.config["LOCAL_PROJECTS"]
        self.project_dir = self._project_dir()
        self.geodiff = GeoDiff()
        self.gediff_log = io.StringIO()

        def _logger_callback(level, text_bytes):
            text = text_bytes.decode()
            if level == GeoDiff.LevelError:
                self.gediff_log.write(f"GEODIFF ERROR: {text} \n")
            elif level == GeoDiff.LevelWarning:
                self.gediff_log.write(f"GEODIFF WARNING: {text} \n")
            else:
                self.gediff_log.write(f"GEODIFF INFO: {text} \n")

        self.geodiff.set_logger_callback(_logger_callback)

    def flush_geodiff_logger(self):
        """Push content to stdout and then reset."""
        logging.warning(self.gediff_log.getvalue())
        self.gediff_log.seek(0)
        self.gediff_log.truncate()

    def _project_dir(self):
        project_dir = os.path.abspath(
            os.path.join(self.projects_dir, self.project.storage_params["location"])
        )
        return project_dir

    def initialize(self, template_project=None):
        if os.path.exists(self.project_dir):
            raise InitializationError(
                "Project directory already exists: {}".format(self.project_dir)
            )

        os.makedirs(self.project_dir)

        if template_project:
            ws = self.project.workspace
            if not ws:
                raise InitializationError("Namespace does not exist")
            if ws.disk_usage() + template_project.disk_usage > ws.storage:
                self.delete()
                raise InitializationError("Disk quota reached")

            for file in template_project.files:
                src = os.path.join(template_project.storage.project_dir, file.location)
                dest = os.path.join(
                    self.project_dir,
                    os.path.join("v1", mergin_secure_filename(file.path)),
                )
                if not os.path.isfile(src):
                    self.restore_versioned_file(file, template_project.latest_version)
                try:
                    copy_file(src, dest)
                except (FileNotFoundError, IOError):
                    self.delete()
                    raise InitializationError(
                        "IOError: failed to copy '{}' to '{}'", src, dest
                    )
                except Exception as e:
                    self.delete()
                    raise InitializationError(str(e))

    def file_size(self, file):
        file_path = os.path.join(self.project_dir, file)
        if not os.path.exists(file_path):
            raise FileNotFound("File {} not found.".format(file))
        return os.path.getsize(file_path)

    def file_path(self, file):
        path = os.path.join(self.project_dir, file)
        if not os.path.exists(path):
            raise FileNotFound("File {} not found.".format(file))
        return path

    def read_file(self, path, block_size=4096):
        file_path = os.path.join(self.project_dir, path)

        # do input validation outside generator to execute immediately
        if not os.path.exists(file_path):
            raise FileNotFound("File {} not found.".format(path))

        def _generator():
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(block_size)
                    sleep(0)
                    if data:
                        yield data
                    else:
                        break

        return _generator()

    # FIXME refactor this into single file action
    def apply_changes(
        self, changes: Dict, version: int, transaction_id: str
    ) -> List[dict]:
        """Apply geodiff changes for gpkg updates. As a result both changeset and full gpkg file are present
        on filesystem. In case of failure DataSyncError is raised. Two possible actions can be done for any update:
        - if diff file is uploaded, then it is applied and new gpkg is constructed
        - if full gpkg is uploaded (e.g. from browser) then corresponding geodiff changeset is calculated
          and diff file saved.
        """
        from ..models import GeodiffActionHistory, ProjectVersion

        updated_files = []
        sync_errors = {}
        modified_files = []
        to_remove = [i["path"] for i in changes["removed"]]
        # filter current project files which are not being removed
        files = list(filter(lambda i: i.path not in to_remove, self.project.files))
        v_name = ProjectVersion.to_v_name(version)

        for f in changes["updated"]:
            # yield to gevent hub since geodiff action can take some time to prevent worker timeout
            sleep(0)
            old_item = next((i for i in files if i.path == f["path"]), None)
            if not old_item:
                sync_errors[f["path"]] = "file does not found on server "
                continue
            updated_file_meta = {
                **f,
                "location": os.path.join(
                    v_name, f.get("sanitized_path", mergin_secure_filename(f["path"]))
                ),
            }
            if "diff" in f:
                basefile = os.path.join(self.project_dir, old_item.location)
                changeset = os.path.join(self.project_dir, v_name, f["diff"]["path"])
                patchedfile = os.path.join(self.project_dir, v_name, f["path"])
                modified_files.append(changeset)
                modified_files.append(patchedfile)
                # create copy of basefile which will be updated in next version
                # TODO this can potentially fail for large files
                logging.info(f"Apply changes: copying {basefile} to {patchedfile}")
                start = time.time()
                copy_file(basefile, patchedfile)
                copy_time = time.time() - start
                logging.info(f"Copying finished in {copy_time} s")
                try:
                    self.flush_geodiff_logger()  # clean geodiff logger
                    logging.info(
                        f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)} "
                        f"with {3} changes to {patchedfile}"
                    )
                    start = time.time()
                    self.geodiff.apply_changeset(patchedfile, changeset)
                    geodiff_apply_time = time.time() - start
                    # track performance of geodiff action
                    base_version = old_item.location.split("/")[0]
                    meta = {**asdict(old_item), "version": ProjectVersion.from_v_name(base_version)}
                    gh = GeodiffActionHistory(
                        self.project.id, meta, v_name, "apply_changes", changeset
                    )
                    gh.copy_time = copy_time
                    gh.geodiff_time = geodiff_apply_time
                    logging.info(f"Changeset applied in {geodiff_apply_time} s")
                except (GeoDiffLibError, GeoDiffLibConflictError):
                    project_workspace = self.project.workspace.name
                    sync_errors[
                        f["path"]
                    ] = f"project: {project_workspace}/{self.project.name}, {self.gediff_log.getvalue()}"
                    continue
                updated_file_meta["diff"]["location"] = os.path.join(
                    v_name,
                    f["diff"].get(
                        "sanitized_path", mergin_secure_filename(f["diff"]["path"])
                    ),
                )
                # we can now replace old basefile metadata with the new one (patchedfile)
                # TODO this can potentially fail for large files
                logging.info(f"Apply changes: calculating checksum of {patchedfile}")
                start = time.time()
                updated_file_meta["checksum"] = generate_checksum(patchedfile)
                checksumming_time = time.time() - start
                gh.checksum_time = checksumming_time
                logging.info(f"Checksum calculated in {checksumming_time} s")
                updated_file_meta["size"] = os.path.getsize(patchedfile)
                db.session.add(gh)
            elif is_versioned_file(f["path"]):
                # diff not provided by client (e.g. web browser), let's try to construct it here
                basefile = os.path.join(self.project_dir, old_item.location)
                uploaded_file = os.path.join(self.project_dir, v_name, f["path"])
                diff_name = f["path"] + "-diff-" + str(uuid.uuid4())
                changeset = os.path.join(self.project_dir, v_name, diff_name)
                try:
                    self.flush_geodiff_logger()
                    logging.info(
                        f"Geodiff: create changeset {changeset} from {uploaded_file}"
                    )
                    self.geodiff.create_changeset(basefile, uploaded_file, changeset)
                    # append diff metadata as it would be created by other clients
                    updated_file_meta["diff"] = {
                        "path": diff_name,
                        "location": os.path.join(
                            v_name, mergin_secure_filename(diff_name)
                        ),
                        "checksum": generate_checksum(changeset),
                        "size": os.path.getsize(changeset),
                    }
                except (GeoDiffLibError, GeoDiffLibConflictError):
                    # diff is not possible to create - file will be overwritten
                    move_to_tmp(changeset)  # remove residuum from geodiff
                    no_diff_in_meta = True
                    logging.warning(
                        f"Geodiff: create changeset error {self.gediff_log.getvalue()}"
                    )

            if f["path"] not in sync_errors:
                updated_files.append(updated_file_meta)

        # do cleanup and exit
        if sync_errors:
            for file in modified_files:
                move_to_tmp(file, transaction_id)
            msg = ""
            for key, value in sync_errors.items():
                msg += key + " error=" + value + "\n"
            raise DataSyncError(msg)

        return updated_files

    def delete(self):
        move_to_tmp(self.project_dir)

    def restore_versioned_file(self, file: str, version: int):
        """
        For removed versioned files tries to restore full file in particular project version
        using file diffs history (latest basefile and sequence of diffs).

        :param file: path of file in project to recover
        :param version: project version (e.g. 2)
        """
        from ..models import GeodiffActionHistory, ProjectVersion

        if not is_versioned_file(file):
            return

        # if project version is not found, return it
        project_version = ProjectVersion.query.filter_by(
            project_id=self.project.id, name=version
        ).first()
        if not project_version:
            return

        # check actual file from the version files
        file_found = next((i for i in project_version.files if i.path == file), None)

        # check the location that we found on the file
        if not file_found or os.path.exists(
            os.path.join(self.project_dir, file_found.location)
        ):
            return

        base_meta, diffs = self.project.file_diffs_chain(file, version)
        if not (base_meta and diffs):
            return

        basefile = os.path.join(self.project_dir, base_meta["location"])
        tmp_dir = os.path.join(current_app.config["TEMP_DIR"], str(uuid.uuid4()))
        os.makedirs(tmp_dir, exist_ok=True)
        restored_file = os.path.join(
            tmp_dir, os.path.basename(basefile)
        )  # this is final restored file
        logging.info(f"Restore file: copying {basefile} to {restored_file}")
        start = time.time()
        copy_file(basefile, restored_file)
        copy_time = time.time() - start
        logging.info(f"File copied in {copy_time} s")
        logging.info(f"Restoring gpkg file with {len(diffs)} diffs")

        try:
            self.flush_geodiff_logger()  # clean geodiff logger
            if len(diffs) > 1:
                # concatenate multiple diffs into single one
                changeset = os.path.join(tmp_dir, os.path.basename(basefile) + "-diff")
                partials = [
                    os.path.join(self.project_dir, d["location"]) for d in diffs
                ]
                self.geodiff.concat_changes(partials, changeset)
            else:
                changeset = os.path.join(self.project_dir, diffs[0]["location"])

            logging.info(
                f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)}"
            )
            # if we are going backwards we need to reverse changeset!
            if base_meta["version"] > version:
                logging.info(f"Geodiff: inverting changeset")
                changes = os.path.join(
                    tmp_dir, os.path.basename(basefile) + "-diff-inv"
                )
                self.geodiff.invert_changeset(changeset, changes)
            else:
                changes = changeset
            start = time.time()
            self.geodiff.apply_changeset(restored_file, changes)
            # track geodiff event for performance analysis
            gh = GeodiffActionHistory(
                self.project.id,
                base_meta,
                ProjectVersion.to_v_name(project_version.name),
                "restore_file",
                changes,
            )
            apply_time = time.time() - start
            gh.geodiff_time = apply_time
            logging.info(f"Changeset applied in {apply_time} s")
        except (GeoDiffLibError, GeoDiffLibConflictError):
            project_workspace = self.project.workspace.name
            logging.exception(
                f"Failed to restore file: {self.gediff_log.getvalue()} from project {project_workspace}/{self.project.name}"
            )
            return
        # move final restored file to place where it is expected (only after it is successfully created)
        logging.info(
            f"Copying restored file to expected location {file_found.location}"
        )
        start = time.time()
        copy_file(restored_file, os.path.join(self.project_dir, file_found.location))
        logging.info(f"File copied in {time.time() - start} s")
        copy_time += time.time() - start
        gh.copy_time = copy_time
        db.session.add(gh)
        db.session.commit()
