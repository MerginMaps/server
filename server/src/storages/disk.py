# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import os
import io
import time
import uuid
import logging
from datetime import datetime
from flask import current_app
from pygeodiff import GeoDiff, GeoDiffLibError
from pygeodiff.geodifflib import GeoDiffLibConflictError
from gevent import sleep
from .storage import ProjectStorage, FileNotFound, DataSyncError, InitializationError
from ..mergin_utils import resolve_tags, generate_checksum, int_version, is_versioned_file
from ..util import mergin_secure_filename


def save_to_file(stream, path, max_size=None):
    """ Save readable object in file while yielding to gevent hub.

    :param stream: object implementing readable interface
    :param path: destination file path
    :param max_size: limit for file size
    """
    directory = os.path.abspath(os.path.dirname(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, 'wb') as output:
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
    """ Custom implementation of copying file by chunk with yielding to gevent hub.

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
    with open(src, 'rb') as input:
        save_to_file(input, dest)


def copy_dir(src, dest):
    """ Custom implementation of recursive copy of directory with yielding to gevent hub.

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
    """ Custom handling of file/directory removal by moving it to regularly cleaned tmp folder.
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
    rel_path = os.path.relpath(src, start=current_app.config['LOCAL_PROJECTS']) # take relative path from parent of all project files
    temp_path = os.path.join(current_app.config['TEMP_DIR'], dest, rel_path)
    os.renames(src, temp_path)
    return temp_path


class DiskStorage(ProjectStorage):

    def __init__(self, project):
        super(DiskStorage, self).__init__(project)
        self.projects_dir = current_app.config['LOCAL_PROJECTS']
        self.project_dir = self._project_dir()
        self.geodiff = GeoDiff()

    def _project_dir(self):
        project_dir = os.path.abspath(
            os.path.join(self.projects_dir, self.project.storage_params["location"])
        )
        return project_dir

    def initialize(self, template_project=None):
        if os.path.exists(self.project_dir):
            raise InitializationError("Project directory already exists: {}".format(self.project_dir))

        os.makedirs(self.project_dir)

        if template_project:
            from ..models.db_models import Namespace
            ns = Namespace.query.filter_by(name=self.project.namespace).first()
            if ns.disk_usage() + template_project.disk_usage > ns.storage:
                self.delete()
                raise InitializationError("Disk quota reached")
            forked_files = []

            for file in template_project.files:
                forked_file = dict(file)
                forked_file['location'] = os.path.join('v1/', file['path'])
                forked_file['mtime'] = datetime.utcnow()
                forked_files.append(forked_file)

                src = os.path.join(template_project.storage.project_dir, file['location'])
                dest = os.path.join(self.project_dir, forked_file['location'])
                try:
                    copy_file(src, dest)
                except (FileNotFoundError, IOError):
                    self.delete()
                    raise InitializationError("IOError: failed to copy '{}' to '{}'", src, dest)
                except Exception as e:
                    self.delete()
                    raise InitializationError(str(e))

            self.project.files = forked_files
            self.project.tags = template_project.tags
            self.project.disk_usage = sum([f['size'] for f in self.project.files])

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
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    sleep(0)
                    if data:
                        yield data
                    else:
                        break

        return _generator()

    def apply_changes(self, changes, version, transaction_id):
        sync_errors = {}
        modified_files = []

        to_remove = [i['path'] for i in changes['removed']]
        files = list(filter(lambda i: i['path'] not in to_remove, self.project.files))
        for item in changes['renamed']:
            renamed = next((i for i in files if i['path'] == item['path']), None)
            if renamed:
                renamed['path'] = item['new_path']
            else:
                sync_errors[item['new_path']] = "renaming error"
                continue

        for f in changes['updated']:
            sleep(0)  # yield to gevent hub since geodiff action can take some time to prevent worker timeout
            old_item = next((i for i in files if i["path"] == f["path"]), None)
            if not old_item:
                sync_errors[f['path']] = "file does not found on server "
                continue
            if 'diff' in f:
                basefile = os.path.join(self.project_dir, old_item["location"])
                changeset = os.path.join(self.project_dir, version, f['diff']['path'])
                patchedfile = os.path.join(self.project_dir, version, f['path'])
                modified_files.append(changeset)
                modified_files.append(patchedfile)
                # create copy of basefile which will be updated in next version
                # TODO this can potentially fail for large files
                logging.info(f"Apply changes: copying {basefile} to {patchedfile}")
                start = time.time()
                copy_file(basefile, patchedfile)
                logging.info(f"Copying finished in {time.time()-start} s")
                try:
                    logging.info(f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)} to {patchedfile}")
                    start = time.time()
                    self.geodiff.apply_changeset(patchedfile, changeset)
                    logging.info(f"Changeset applied in {time.time() - start} s")
                except (GeoDiffLibError, GeoDiffLibConflictError) as err:
                    sync_errors[f["path"]] = f"project: {self.project.namespace}/{self.project.name}, geodiff error {str(err)}"
                    continue

                f["diff"]["location"] = os.path.join(
                    version, f['diff']['sanitized_path'] if 'sanitized_path' in f['diff'] else mergin_secure_filename(f['diff']['path']))

                # we can now replace old basefile metadata with the new one (patchedfile)
                # TODO this can potentially fail for large files
                logging.info(f"Apply changes: calculating checksum of {patchedfile}")
                start = time.time()
                f['checksum'] = generate_checksum(patchedfile)
                logging.info(f"Checksum calculated in {time.time() - start} s")
                f['size'] = os.path.getsize(patchedfile)
            else:
                old_item.pop("diff", None)

            if 'chunks' in f:
                f.pop("chunks")
            f['location'] = os.path.join(
                version,
                f['sanitized_path'] if 'sanitized_path' in f else mergin_secure_filename(f['path']))
            if not sync_errors:
                old_item.update(f)

        if sync_errors:
            for file in modified_files:
                move_to_tmp(file, transaction_id)
            msg = ""
            for key, value in sync_errors.items():
                msg += key + " error=" + value + "\n"
            raise DataSyncError(msg)

        for item in changes['added']:
            files.append({
                'path': item['path'],
                'size': item['size'],
                'checksum': item['checksum'],
                'mtime': item['mtime'],
                'location': os.path.join(
                    version,
                    item['sanitized_path'] if 'sanitized_path' in item else mergin_secure_filename(item['path']))
            })

        self.project.files = files
        self.project.tags = resolve_tags(files)

    def delete(self):
        move_to_tmp(self.project_dir)

    def optimize_storage(self):
        """ Optimize disk storage for project.

        Clean up for recently updated versioned files. Removes expired file versions.
        It applies only on files that can be recreated when needed.
        """
        files = [f for f in self.project.files if 'diff' in f.keys()]
        last_version = sorted(self.project.versions, key=lambda ver: int_version(ver.name))[-1]
        for f in files:
            f_history = self.project.file_history(f['path'], 'v1', last_version.name)
            if not f_history:
                continue
            for item in f_history.values():
                if 'diff' in item:
                    if item['location'] == f['location']:
                        continue  # skip latest file version
                    abs_path = os.path.join(self.project_dir, item['location'])
                    if not os.path.exists(abs_path):
                        continue  # already removed
                    age = time.time() - os.path.getmtime(abs_path)
                    if age > current_app.config['FILE_EXPIRATION']:
                        move_to_tmp(abs_path)

    def restore_versioned_file(self, file, version):
        """
        For removed versioned files tries to restore full file in particular project version
        using file diffs history (latest basefile and sequence of diffs).

        :param file: path of file in project to recover
        :type file: str
        :param version: project version (e.g. v2)
        :type version: str
        """
        if not is_versioned_file(file):
            return

        # if project version is not found, return it
        project_version = next((v for v in self.project.versions if v.name == version), None)
        if not project_version:
            return

        # check actual file from the version files
        file_found = next((i for i in project_version.files if i['path'] == file), None)

        # check the location that we found on the file
        if not file_found or os.path.exists(os.path.join(self.project_dir, file_found['location'])):
            return

        basefile_meta = {}
        diffs = []
        f_history = self.project.file_history(file, 'v1', version)
        if not f_history:
            return
        # history starts from the latest change, we stop when reaching basefile
        for item in f_history.values():
            if item['change'] in ['added', 'updated']:
                if 'diff' in item:
                    diffs.append(item['diff'])
                else:
                    basefile_meta = item
                    break
            else:
                continue

        if not (basefile_meta and diffs):
            return

        basefile = os.path.join(self.project_dir, basefile_meta['location'])
        tmp_dir = os.path.join(current_app.config['TEMP_DIR'], str(uuid.uuid4()))
        os.mkdir(tmp_dir)
        restored_file = os.path.join(tmp_dir, os.path.basename(basefile))  # this is final restored file
        logging.info(f"Restore file: copying {basefile} to {restored_file}")
        start = time.time()
        copy_file(basefile, restored_file)
        logging.info(f"File copied in {time.time() - start} s")
        logging.info(f"Restoring gpkg file with {len(diffs)} diffs")
        for diff in reversed(diffs):
            sleep(0)  # yield to gevent hub since geodiff action can take some time, and in case of a lot of diffs it could time out
            changeset = os.path.join(self.project_dir, diff['location'])
            try:
                logging.info(f"Geodiff: apply changeset {changeset} of size {os.path.getsize(changeset)}")
                start = time.time()
                self.geodiff.apply_changeset(restored_file, changeset)
                logging.info(f"Changeset applied in {time.time() - start} s")
            except (GeoDiffLibError, GeoDiffLibConflictError) as e:
                logging.exception(f"Failed to restore file: {str(e)} from project {self.project.namespace}/{self.project.name}")
                return
        # move final restored file to place where it is expected (only after it is successfully created)
        logging.info(f"Copying restored file to expected location {file_found['location']}")
        start = time.time()
        copy_file(restored_file, os.path.join(self.project_dir, file_found['location']))
        logging.info(f"File copied in {time.time() - start} s")
