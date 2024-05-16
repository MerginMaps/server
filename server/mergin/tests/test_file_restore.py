# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import os
import pytest
import shutil
from sqlalchemy.orm.attributes import flag_modified

from .. import db
from ..auth.models import User
from ..sync.models import ProjectVersion, Project, GeodiffActionHistory
from . import test_project_dir, TMP_DIR
from .utils import (
    create_project,
    create_workspace,
    gpkgs_are_equal,
    create_blank_version,
    execute_query,
    push_change,
)


def _prepare_restore_project(working_dir: str) -> Project:
    """Prepare new project with basefile called base.gpkg from testing files"""
    user = User.query.filter_by(username="mergin").first()
    test_workspace = create_workspace()
    project = create_project("restore_test", test_workspace, user)

    # cleanup
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)

    os.makedirs(working_dir, exist_ok=True)
    # add basefile
    shutil.copy(
        os.path.join(test_project_dir, "base.gpkg"),
        os.path.join(working_dir, "base.gpkg"),
    )
    push_change(project, "added", "base.gpkg", working_dir)
    assert project.latest_version == "v1"
    assert os.path.exists(os.path.join(project.storage.project_dir, "v1", "base.gpkg"))
    return project


@pytest.mark.parametrize("forward_check", [True, False])
def test_crud_in_version_file_restore(app, forward_check):
    """Test to restore gpkg file where feature went through CRUD operations in subsequent versions"""
    working_dir = os.path.join(TMP_DIR, "restore_from_diffs_with_crud")
    basefile = os.path.join(working_dir, "base.gpkg")
    p = _prepare_restore_project(working_dir)

    # introduce dummy changes to project before making any updated to force restore lookup from the end
    if not forward_check:
        for _ in range(3):
            create_blank_version(p)

    # insert new feature
    sql = "INSERT INTO simple (geometry, name) VALUES (GeomFromText('POINT(24.5, 38.2)', 4326), 'insert_test')"
    execute_query(basefile, sql)
    pv2 = push_change(p, "updated", "base.gpkg", working_dir)
    assert p.latest_version == pv2.name
    assert os.path.exists(os.path.join(p.storage.project_dir, pv2.name, "base.gpkg"))
    # update feature
    sql = "UPDATE simple SET rating=100 WHERE name='insert_test'"
    execute_query(basefile, sql)
    pv3 = push_change(p, "updated", "base.gpkg", working_dir)
    assert p.latest_version == pv3.name
    assert os.path.exists(os.path.join(p.storage.project_dir, pv3.name, "base.gpkg"))
    # delete feature
    sql = "DELETE FROM simple WHERE name='insert_test'"
    execute_query(basefile, sql)
    pv4 = push_change(p, "updated", "base.gpkg", working_dir)
    assert p.latest_version == pv4.name
    assert os.path.exists(os.path.join(p.storage.project_dir, pv4.name, "base.gpkg"))

    # introduce dummy changes before last project update to force restore lookup from beginning
    if forward_check:
        for _ in range(3):
            create_blank_version(p)

    # create new version, latest is also 'basefile' from restore point of view
    sql = "UPDATE simple SET rating=100 WHERE fid=1"
    execute_query(basefile, sql)
    pv5 = push_change(p, "updated", "base.gpkg", working_dir)
    assert p.latest_version == pv5.name
    assert os.path.exists(os.path.join(p.storage.project_dir, pv5.name, "base.gpkg"))

    # tests we can restore anything between pv1 and pv5
    for version in [pv2.name, pv3.name, pv4.name]:
        test_file = os.path.join(p.storage.project_dir, version, "base.gpkg")
        os.rename(test_file, test_file + "_backup")
        p.storage.restore_versioned_file("base.gpkg", version)
        assert os.path.exists(test_file)
        assert gpkgs_are_equal(test_file, test_file + "_backup")


@pytest.mark.parametrize("forward_check", [True, False])
def test_version_file_restore_with_no_changes(app, forward_check):
    """Test to restore gpkg file from diffs where history contains some blank versions (no changes)."""
    working_dir = os.path.join(TMP_DIR, "restore_from_diffs_with_gaps")
    basefile = os.path.join(working_dir, "base.gpkg")
    p = _prepare_restore_project(working_dir)

    if not forward_check:
        for _ in range(6):
            create_blank_version(p)

    base_version = p.get_latest_version().int_name
    for i in range(3):
        sql = "INSERT INTO simple (geometry, name) VALUES (GeomFromText('POINT(24.5, 38.2)', 4326), 'insert_test')"
        execute_query(basefile, sql)
        pv_latest = push_change(p, "updated", "base.gpkg", working_dir)
        assert p.latest_version == pv_latest.name
        assert os.path.exists(
            os.path.join(p.storage.project_dir, pv_latest.name, "base.gpkg")
        )
        # create "no changes" version
        create_blank_version(p)

    latest_version = p.get_latest_version().int_name
    # reconstruct all "diff" file versions including those where no changes were made
    # but not first basefile and full latest version
    for ver in range(base_version + 1, latest_version - 1):
        pv = ProjectVersion.query.filter_by(
            project_id=str(p.id), name=f"v{ver}"
        ).first()
        file = next(i for i in pv.files if i["path"] == "base.gpkg")
        expected_file = os.path.join(p.storage.project_dir, file["location"])
        # pretend previous full file was removed due to storage optimization
        os.rename(expected_file, expected_file + "_backup")

        p.storage.restore_versioned_file("base.gpkg", pv.name)
        assert os.path.exists(expected_file)
        assert gpkgs_are_equal(expected_file + "_backup", expected_file)


def test_version_file_restore(diff_project):
    """Test restore gpkg file with history which contains deletion, force update and renaming (legacy option)"""
    test_file = os.path.join(diff_project.storage.project_dir, "v4", "base.gpkg")
    os.rename(test_file, test_file + "_backup")
    diff_project.storage.restore_versioned_file("base.gpkg", "v4")
    assert os.path.exists(test_file)
    assert gpkgs_are_equal(test_file, test_file + "_backup")

    # we can restore version 7 (composed from multiple diffs from v6 and v7)
    test_file = os.path.join(diff_project.storage.project_dir, "v7", "base.gpkg")
    os.rename(test_file, test_file + "_backup")
    diff_project.storage.restore_versioned_file("base.gpkg", "v7")
    assert os.path.exists(test_file)
    assert gpkgs_are_equal(test_file, test_file + "_backup")
    # check we track performance of reconstruction
    gh = GeodiffActionHistory.query.filter_by(
        project_id=diff_project.id, target_version="v7"
    ).first()
    assert gh.base_version == "v5"
    assert gh.geodiff_time
    assert gh.copy_time
    assert gh.action == "restore_file"

    # restore v6 from previous basefile v5
    test_file = os.path.join(diff_project.storage.project_dir, "v6", "base.gpkg")
    os.rename(test_file, test_file + "_backup")
    diff_project.storage.restore_versioned_file("base.gpkg", "v6")
    assert os.path.exists(test_file)
    assert gpkgs_are_equal(test_file, test_file + "_backup")

    # remove v9 and v10 to mimic that project history end with existing file
    pv_8 = ProjectVersion.query.filter_by(project_id=diff_project.id, name="v8").first()
    pv_9 = ProjectVersion.query.filter_by(project_id=diff_project.id, name="v9").first()
    pv_10 = ProjectVersion.query.filter_by(
        project_id=diff_project.id, name="v10"
    ).first()
    diff_project.latest_version = "v8"
    db.session.delete(pv_9)
    db.session.delete(pv_10)
    db.session.commit()
    # restore v6 backward, from the latest file (v7=v8)
    test_file = os.path.join(diff_project.storage.project_dir, "v6", "base.gpkg")
    if os.path.exists(test_file):
        os.remove(test_file)
    diff_project.storage.restore_versioned_file("base.gpkg", "v6")
    assert os.path.exists(test_file)
    assert gpkgs_are_equal(test_file, test_file + "_backup")
    gh = GeodiffActionHistory.query.filter_by(
        project_id=diff_project.id, base_version="v7", target_version="v6"
    ).first()
    assert gh.geodiff_time
    assert gh.copy_time

    # basefile can not be restored
    test_file = os.path.join(diff_project.storage.project_dir, "v5", "base.gpkg")
    os.remove(test_file)
    diff_project.storage.restore_versioned_file("base.gpkg", "v5")
    assert not os.path.exists(test_file)

    # no geodiff file can not be restored
    test_file = os.path.join(diff_project.storage.project_dir, "v1", "test.txt")
    os.remove(test_file)
    diff_project.storage.restore_versioned_file("test.txt", "v1")
    assert not os.path.exists(test_file)
