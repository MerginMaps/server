# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import os
import tempfile
import shutil
import pytest
from src.storages.disk import copy_file, copy_dir, move_to_tmp
from src.mergin_utils import generate_checksum
from . import test_project_dir


def test_copy_remove_file(app):
    f_old = os.path.join(test_project_dir, 'base.gpkg')
    f_new = os.path.join(tempfile.gettempdir(), 'base.gpkg')
    # clean up
    if os.path.exists(f_new):
        os.remove(f_new)

    copy_file(f_old, f_new)
    assert os.path.exists(f_new)
    f_new_hash = generate_checksum(f_new)
    assert f_new_hash == generate_checksum(f_old)

    f_temp = move_to_tmp(f_new)
    assert not os.path.exists(f_new)
    assert os.path.exists(f_temp)
    assert generate_checksum(f_temp) == f_new_hash


def test_copy_remove_dir(app):
    d_old = test_project_dir
    d_new = os.path.join(tempfile.gettempdir(), 'new_dir')
    # clean up
    if os.path.exists(d_new):
        shutil.rmtree(d_new)

    copy_dir(d_old, d_new)
    assert os.path.exists(d_new)
    copied_files = []
    for root, dirs, files in os.walk(d_old):
        for file in files:
            abs_path = os.path.abspath(os.path.join(root, file))
            rel_path = os.path.relpath(abs_path, start=d_old)
            f_copy = os.path.join(d_new, rel_path)
            assert os.path.exists(f_copy)
            assert generate_checksum(abs_path) == generate_checksum(f_copy)
            copied_files.append(rel_path)

    d_temp = move_to_tmp(d_new)
    assert not os.path.exists(d_new)
    assert os.path.exists(d_temp)
    for f in copied_files:
        assert os.path.exists(os.path.join(d_temp, f))

    # try again to remove
    assert not move_to_tmp(d_new)


def test_failures():
    # file copy source/destination is not a file type
    with pytest.raises(IsADirectoryError):
        copy_file(os.path.join(test_project_dir, 'base.gpkg'), tempfile.gettempdir())

    with pytest.raises(FileNotFoundError):
        copy_file(test_project_dir, os.path.join(tempfile.gettempdir(), 'base.gpkg'))

    # src file does not exist
    with pytest.raises(FileNotFoundError):
        copy_file(os.path.join(test_project_dir, 'not-found.gpkg'), os.path.join(tempfile.gettempdir(), 'base.gpkg'))

    # src directory is not valid
    with pytest.raises(NotADirectoryError):
        copy_dir(os.path.join(test_project_dir, 'base.gpkg'), os.path.join(tempfile.gettempdir(), 'new_dir'))

    with pytest.raises(NotADirectoryError):
        copy_dir(os.path.join(test_project_dir, 'not_found'), os.path.join(tempfile.gettempdir(), 'new_dir'))
