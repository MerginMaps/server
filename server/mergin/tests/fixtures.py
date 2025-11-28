# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
import shutil
import sys
import uuid
from shutil import copy, move
from flask import current_app
from sqlalchemy import desc
from pygeodiff import GeoDiff
import pytest

from ..app import db, create_app
from ..sync.models import Project, ProjectVersion
from ..stats.models import MerginInfo
from . import test_project, test_workspace_id, test_project_dir, TMP_DIR
from .utils import login_as_admin, initialize, cleanup, file_info
from ..sync.files import files_changes_from_upload

thisdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(thisdir, os.pardir))


@pytest.fixture(scope="function")
def flask_app(request):
    """Flask app with fresh db and initialized empty tables"""
    from ..sync.db_events import remove_events
    from ..app import register as register_bp
    from ..stats.config import Configuration as StatsConfig

    application = create_app(
        [
            "SERVER_TYPE",
            "DOCS_URL",
            "COLLECT_STATISTICS",
            "USER_SELF_REGISTRATION",
            "V2_PUSH_ENABLED",
        ]
    )
    application.config["TEST_DIR"] = os.path.join(thisdir, "test_projects")
    application.config["SERVER_NAME"] = "localhost.localdomain"
    application.config["SERVER_TYPE"] = "ce"
    application.config["SERVICE_ID"] = str(uuid.uuid4())

    # add stats module
    register_bp(application, "stats", StatsConfig, "../mergin/stats/api.yaml")
    app_context = application.app_context()
    app_context.push()

    with app_context:
        db.create_all()

    def teardown():
        # clean up db
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

        app_context.pop()
        # detach db hooks
        remove_events()

    request.addfinalizer(teardown)
    return application


@pytest.fixture(scope="function")
def app(flask_app, request):
    """Flask app with testing objects created"""
    with flask_app.app_context():
        initialize()
        info = MerginInfo(service_id=current_app.config["SERVICE_ID"])
        db.session.add(info)
        db.session.commit()

    def teardown():
        # remove all project files
        with flask_app.app_context():
            dirs = [
                p.storage.project_dir
                for p in Project.query.all()
                if p.storage is not None
            ]
            cleanup(flask_app.test_client(), dirs)
            diagnostic_logs_dir = flask_app.config.get("DIAGNOSTIC_LOGS_DIR")
            if os.path.exists(diagnostic_logs_dir):
                shutil.rmtree(diagnostic_logs_dir)

    request.addfinalizer(teardown)
    return flask_app


@pytest.fixture(scope="function")
def client(app):
    """Flask app tests client with already logged-in superuser"""
    client = app.connexion_app.test_client()
    login_as_admin(client)
    return client


@pytest.fixture(scope="function")
def diff_project(app):
    """Modify testing project to contain some history with diffs. Geodiff lib is used to handle changes.
    Files are copied to location where server would expect it. Corresponding changes metadata and project versions
    are created and stored in db.

    Following changes are applied to base.gpkg in tests project (v1):
    v2: removed file -> previous version is lost (unless requested explicitly)
    v3: uploaded again -> new basefile
    v4: patched with changes from inserted_1_A.gpkg (1 inserted feature)
    v5: replaced with original file base.gpkg (mimic of force update) -> new basefile again
    v6: patched with changes from modified_1_geom.gpkg (translated feature)
    v7: patched with changes from inserted_1_B.gpkg (1 inserted feature), final state is modified_1_geom.gpkg + inserted_1_B.gpkg
    v8: nothing happened, just to ensure last diff is not last version of project file
    v9: renamed to test.gpkg base.gpkg has been removed and tests.gpkg has been added
    v10: nothing happened (although officially forbidden here it mimics no changes to file of interest)
    """
    from .test_project_controller import create_diff_meta

    test_gpkg_file = os.path.join(test_project_dir, "test.gpkg")
    try:
        geodiff = GeoDiff()
        project = Project.query.filter_by(
            name=test_project, workspace_id=test_workspace_id
        ).first()

        update_meta = file_info(test_project_dir, "base.gpkg")
        diff_meta_A = create_diff_meta(
            "base.gpkg", "inserted_1_A.gpkg", test_project_dir
        )
        diff_meta_mod = create_diff_meta(
            "base.gpkg", "modified_1_geom.gpkg", test_project_dir
        )

        patch = os.path.join(TMP_DIR, "patch")

        basefile = os.path.join(test_project_dir, "base.gpkg")
        copy(basefile, patch)
        copy(basefile, test_gpkg_file)
        geodiff.apply_changeset(
            patch, os.path.join(TMP_DIR, diff_meta_mod["diff"]["path"])
        )
        diff_meta_B = create_diff_meta(
            "base.gpkg", "inserted_1_B.gpkg", test_project_dir
        )

        changes = [
            {
                "added": [],
                "removed": [file_info(test_project_dir, "base.gpkg")],
                "updated": [],
            },
            {
                "added": [file_info(test_project_dir, "base.gpkg")],
                "removed": [],
                "updated": [],
            },
            {"added": [], "removed": [], "updated": [diff_meta_A]},
            # force update with full file
            {
                "added": [],
                "removed": [],
                "updated": [update_meta],
            },
            {"added": [], "removed": [], "updated": [diff_meta_mod]},
            {"added": [], "removed": [], "updated": [diff_meta_B]},
            # final state of base.gpkg (v8)
            {
                "added": [],
                "removed": [],
                "updated": [],
            },
            # file renamed, by removing old and upload new - break of history
            {
                "added": [file_info(test_project_dir, "test.gpkg")],
                "removed": [file_info(test_project_dir, "base.gpkg")],
                "updated": [],
            },
            {"added": [], "removed": [], "updated": []},
        ]
        for i, change in enumerate(changes):
            ver = f"v{i + 2}"
            if change["added"]:
                file_meta = change["added"][0]
                new_file = os.path.join(
                    project.storage.project_dir, ver, file_meta["path"]
                )
                os.makedirs(os.path.dirname(new_file), exist_ok=True)
                copy(os.path.join(test_project_dir, file_meta["path"]), new_file)
            elif change["updated"]:
                file_meta = change["updated"][0]
                f_updated = next(
                    f for f in project.files if f.path == file_meta["path"]
                )
                patchedfile = os.path.join(
                    project.storage.project_dir, ver, f_updated.path
                )
                os.makedirs(os.path.dirname(patchedfile), exist_ok=True)
                if "diff" in file_meta:
                    basefile = os.path.join(
                        project.storage.project_dir, f_updated.location
                    )
                    changefile = os.path.join(TMP_DIR, file_meta["diff"]["path"])
                    copy(basefile, patchedfile)
                    geodiff.apply_changeset(patchedfile, changefile)
                    move(
                        changefile,
                        os.path.join(
                            project.storage.project_dir, ver, file_meta["diff"]["path"]
                        ),
                    )
                else:
                    copy(os.path.join(test_project_dir, f_updated.path), patchedfile)
            else:
                # no files uploaded, hence no action needed
                pass

            file_changes = files_changes_from_upload(change, location_dir=f"v{i + 2}")
            pv = ProjectVersion(
                project,
                i + 2,
                project.creator.id,
                file_changes,
                "127.0.0.1",
            )
            assert pv.project_size == sum(file.size for file in pv.files)
            db.session.add(pv)
            db.session.add(project)
            latest_version = (
                ProjectVersion.query.filter_by(project_id=project.id)
                .order_by(desc(ProjectVersion.created))
                .first()
            )
            assert latest_version.project_size == sum(
                file.size for file in latest_version.files
            )

        db.session.add(project)
        db.session.commit()
    finally:
        os.remove(test_gpkg_file)
    return project


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_migration(client):
    resp = client.post(
        "/app/auth/login",
        json={"login": "mergin", "password": "ilovemergin"},
    )
    assert resp.status_code == 200

    p = Project.query.first()
    resp = client.get(
        f"/v2/projects/{p.id}",
    )
    assert resp.status_code == 200

    resp = client.get("/app/project/templates")
    assert resp.status_code == 200

    resp = client.get(
        f"/v1/project/{p.workspace.name}/{p.name}",
    )
    assert resp.status_code == 200

    # this is not working as v1 already registered with project api
    # resp = client.get(
    #     "/v1/user/profile"
    # )
    # assert resp.status_code == 200

    resp = client.get(
        "/app/auth/logout",
    )

    assert resp.status_code == 200
