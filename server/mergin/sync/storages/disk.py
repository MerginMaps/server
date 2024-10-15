# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
import io
import tempfile
import time
import uuid
import logging
from contextlib import contextmanager

from flask import current_app
from pygeodiff import GeoDiff, GeoDiffLibError
from pygeodiff.geodifflib import GeoDiffLibConflictError
from gevent import sleep
from result import Err, Ok, Result

from .storage import ProjectStorage, FileNotFound, InitializationError
from ... import db
from ..utils import (
    generate_checksum,
    is_versioned_file,
)
from ..files import mergin_secure_filename, ProjectFile, UploadFile, File


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
    temp_path = os.path.join(
        current_app.config["TEMP_DIR"], dest, os.path.basename(src)
    )
    try:
        os.renames(src, temp_path)
    except OSError as e:
        # in the case of specific cross-device error [Errno 18] Invalid cross-device link
        # just rename it within the same root with prefix 'delete-me' for easier custom cleanup
        if e.errno == 18:
            if src.startswith(current_app.config["LOCAL_PROJECTS"]):
                root = current_app.config["LOCAL_PROJECTS"]
            elif src.startswith(current_app.config["GEODIFF_WORKING_DIR"]):
                root = current_app.config["GEODIFF_WORKING_DIR"]
            else:
                root = tempfile.gettempdir()
            temp_path = os.path.join(root, "delete-me-" + dest, os.path.basename(src))
            os.renames(src, temp_path)
        else:
            raise
    return temp_path


class DiskStorage(ProjectStorage):
    def __init__(self, project):
        super(DiskStorage, self).__init__(project)
        self.projects_dir = current_app.config["LOCAL_PROJECTS"]
        self.project_dir = self._project_dir()
        self.geodiff = GeoDiff()
        self.gediff_log = io.StringIO()
        self.geodiff_working_dir = os.path.abspath(
            os.path.join(
                current_app.config["GEODIFF_WORKING_DIR"],
                self.project.storage_params["location"],
                str(uuid.uuid4()),
            )
        )

        def _logger_callback(level, text_bytes):
            text = text_bytes.decode()
            if level == GeoDiff.LevelError:
                self.gediff_log.write(f"GEODIFF ERROR: {text} \n")
            elif level == GeoDiff.LevelWarning:
                self.gediff_log.write(f"GEODIFF WARNING: {text} \n")
            else:
                self.gediff_log.write(f"GEODIFF INFO: {text} \n")

        self.geodiff.set_logger_callback(_logger_callback)

    @contextmanager
    def geodiff_copy(self, file):
        """Copy project file from live storage to geodiff temp storage for further actions.
        If file cannot be copied then as a fallback it creates _tmp file next to original file.
        Temporary copy is removed on exit.
        """
        file_path = file.replace(self.project_dir, "").lstrip(os.path.sep)
        file_copy = os.path.join(self.geodiff_working_dir, file_path)
        try:
            copy_file(file, file_copy)
            yield file_copy
        except OSError as e:
            logging.warning(f"Copy to geodiff dir failed: {str(e)}")
            # fallback to live directory
            file_copy = file + "_tmp"
            copy_file(file, file_copy)
            yield file_copy
        finally:
            move_to_tmp(file_copy)

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

    def apply_diff(
        self, current_file: ProjectFile, upload_file: UploadFile, version: int
    ) -> Result:
        """Apply geodiff diff file on current gpkg basefile. Creates GeodiffActionHistory record of the action.
        Returns checksum and size of generated file. If action fails it returns geodiff error message.
        """
        from ..models import GeodiffActionHistory, ProjectVersion

        v_name = ProjectVersion.to_v_name(version)
        basefile = os.path.join(self.project_dir, current_file.location)
        changeset = os.path.join(self.project_dir, upload_file.diff.location)
        patchedfile = os.path.join(self.project_dir, upload_file.location)
        # create local copy of basefile which will be updated in next version and changeset needed
        # TODO this can potentially fail for large files
        logging.info(f"Apply changes: copying {basefile} to {patchedfile}")
        start = time.time()
        with self.geodiff_copy(changeset) as changeset_tmp, self.geodiff_copy(
            basefile
        ) as patchedfile_tmp:
            copy_time = time.time() - start
            logging.info(f"Copying finished in {copy_time} s")
            try:
                # clean geodiff logger
                self.flush_geodiff_logger()
                logging.info(
                    f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)} with changes to {patchedfile}"
                )
                start = time.time()
                self.geodiff.apply_changeset(patchedfile_tmp, changeset_tmp)
                geodiff_apply_time = time.time() - start
                # track performance of geodiff action
                base_version = current_file.location.split("/")[0]
                gh = GeodiffActionHistory(
                    self.project.id,
                    base_version,
                    current_file.path,
                    current_file.size,
                    v_name,
                    "apply_changes",
                    changeset,
                )
                gh.copy_time = copy_time
                gh.geodiff_time = geodiff_apply_time
                logging.info(f"Changeset applied in {geodiff_apply_time} s")
                # move constructed file where is belongs
                logging.info(f"Apply changes: moving patchfile {patchedfile_tmp}")
                start = time.time()
                copy_file(patchedfile_tmp, patchedfile)
                gh.copy_time = copy_time + (time.time() - start)

                # TODO this can potentially fail for large files
                logging.info(f"Apply changes: calculating checksum of {patchedfile}")
                start = time.time()
                checksum = generate_checksum(patchedfile_tmp)
                checksumming_time = time.time() - start
                gh.checksum_time = checksumming_time
                logging.info(f"Checksum calculated in {checksumming_time} s")
                db.session.add(gh)
                return Ok(
                    (
                        checksum,
                        os.path.getsize(patchedfile_tmp),
                    )
                )
            except (GeoDiffLibError, GeoDiffLibConflictError):
                move_to_tmp(changeset)
                return Err(self.gediff_log.getvalue())

    def construct_diff(
        self, current_file: ProjectFile, upload_file: UploadFile, version: int
    ) -> Result:
        """Construct geodiff diff file from uploaded gpkg and current basefile. Returns diff metadata as a result.
        If action fails it returns geodiff error message.
        """
        from ..models import ProjectVersion

        v_name = ProjectVersion.to_v_name(version)
        basefile = os.path.join(self.project_dir, current_file.location)
        uploaded_file = os.path.join(self.project_dir, upload_file.location)
        diff_name = upload_file.path + "-diff-" + str(uuid.uuid4())
        changeset = os.path.join(self.project_dir, v_name, diff_name)
        with self.geodiff_copy(basefile) as basefile_tmp, self.geodiff_copy(
            uploaded_file
        ) as uploaded_file_tmp:
            try:
                # create changeset next to uploaded file copy
                changeset_tmp = os.path.join(
                    uploaded_file_tmp.replace(upload_file.location, "").rstrip(
                        os.path.sep
                    ),
                    v_name,
                    diff_name,
                )
                self.flush_geodiff_logger()
                logging.info(
                    f"Geodiff: create changeset {changeset} from {uploaded_file}"
                )
                self.geodiff.create_changeset(
                    basefile_tmp, uploaded_file_tmp, changeset_tmp
                )
                # create diff metadata as it would be created by other clients
                diff_file = File(
                    path=diff_name,
                    checksum=generate_checksum(changeset_tmp),
                    size=os.path.getsize(changeset_tmp),
                    location=os.path.join(v_name, mergin_secure_filename(diff_name)),
                )
                copy_file(changeset_tmp, changeset)
                return Ok(diff_file)
            except (GeoDiffLibError, GeoDiffLibConflictError) as e:
                # diff is not possible to create - file will be overwritten
                move_to_tmp(changeset)
                return Err(self.gediff_log.getvalue())
            finally:
                move_to_tmp(changeset_tmp)

    def delete(self):
        move_to_tmp(self.project_dir)

    def restore_versioned_file(self, file: str, version: int):
        """
        For removed versioned files tries to restore full file in particular project version
        using file diffs history (latest basefile and sequence of diffs).

        :param file: path of file in project to recover
        :param version: project version (e.g. 2)
        """
        from ..models import GeodiffActionHistory, ProjectVersion, FileHistory

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

        base_meta, diffs = FileHistory.diffs_chain(self.project, file, version)
        if not (base_meta and diffs):
            return

        start = time.time()
        with self.geodiff_copy(base_meta.abs_path) as restored_file:
            copy_time = time.time() - start
            logging.info(
                f"Restore file: {base_meta.abs_path} copied to {restored_file} in {copy_time} s"
            )
            logging.info(f"Restoring gpkg file with {len(diffs)} diffs")
            try:
                self.flush_geodiff_logger()  # clean geodiff logger
                changeset = os.path.join(
                    self.geodiff_working_dir,
                    os.path.basename(base_meta.abs_path) + "-diff",
                )
                if len(diffs) > 1:
                    # concatenate multiple diffs into single one
                    partials = [
                        os.path.join(self.project_dir, d.location) for d in diffs
                    ]
                    self.geodiff.concat_changes(partials, changeset)
                else:
                    copy_file(
                        os.path.join(self.project_dir, diffs[0].location), changeset
                    )

                logging.info(
                    f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)}"
                )
                # if we are going backwards we need to reverse changeset!
                if base_meta.version.name > version:
                    logging.info(f"Geodiff: inverting changeset")
                    changes = os.path.join(
                        self.geodiff_working_dir,
                        os.path.basename(base_meta.abs_path) + "-diff-inv",
                    )
                    self.geodiff.invert_changeset(changeset, changes)
                else:
                    changes = changeset

                start = time.time()
                self.geodiff.apply_changeset(restored_file, changes)
                # track geodiff event for performance analysis
                gh = GeodiffActionHistory(
                    self.project.id,
                    ProjectVersion.to_v_name(base_meta.version.name),
                    base_meta.path,
                    base_meta.size,
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
            finally:
                move_to_tmp(changes)
                move_to_tmp(changeset)
            # move final restored file to place where it is expected (only after it is successfully created)
            logging.info(
                f"Copying restored file to expected location {file_found.location}"
            )
            start = time.time()
            copy_file(
                restored_file, os.path.join(self.project_dir, file_found.location)
            )
            logging.info(f"File copied in {time.time() - start} s")
            copy_time += time.time() - start
            gh.copy_time = copy_time
            db.session.add(gh)
            db.session.commit()
