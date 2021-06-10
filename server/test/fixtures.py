import os
import sys
from shutil import copy, move
from sqlalchemy.orm.attributes import flag_modified
from pygeodiff import GeoDiff
import pytest


from src import db, create_app
from src.db_events import remove_events
from src.models.db_models import (Project, Upload, ProjectVersion, ProjectAccess, ProjectTransfer,
                                  Namespace, Account, RemovedProject)
from src.mergin_utils import generate_checksum, is_versioned_file, resolve_tags
from src.auth.models import User, UserProfile
from src.organisation.models import Organisation

from . import test_project, test_namespace, test_project_dir, TMP_DIR, TEST_ORG, DEFAULT_USER
from .test_project_controller import _file_info, create_diff_meta
from .utils import login_as_admin, add_user, initialize, cleanup

thisdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(thisdir, os.pardir))


@pytest.fixture(scope='function')
def flask_app(request):
    """ Flask app with fresh db and initialized empty tables """
    application = create_app()
    application.config['TEST_DIR'] = os.path.join(thisdir, 'test_projects')
    application.config['SERVER_NAME'] = 'localhost.localdomain'
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


@pytest.fixture(scope='function')
def app(flask_app, request):
    """ Flask app with testing objects created """
    with flask_app.app_context():
        initialize()

    def teardown():
        # remove all project files
        with flask_app.app_context():
            dirs = [p.storage.project_dir for p in Project.query.all()]
            print(dirs)
            cleanup(flask_app.test_client(), dirs)

    request.addfinalizer(teardown)
    return flask_app


@pytest.fixture(scope='function')
def client(app):
    """ Flask app test client with already logged-in superuser """
    client = app.test_client()
    login_as_admin(client)
    return client


@pytest.fixture(scope='function')
def diff_project(app):
    """ Modify testing project to contain some history with diffs. Geodiff lib is used to handle changes.
    Files are copied to location where server would expect it. Corresponding changes metadata and project versions
    are created and stored in db.

    Following changes are applied to base.gpkg in test project (v1):
    v2: removed file -> previous version is lost (unless requested explicitly)
    v3: uploaded again
    v4: patched with changes from inserted_1_A.gpkg (1 inserted feature)
    v5: replaced with original file base.gpkg (mimic of force update)
    v6: patched with changes from modified_1_geom.gpkg (translated feature)
    v7: renamed to test.gpkg
    v8: nothing happened (although officially forbidden here it mimics no changes to file of interest)
    v9: test.gpkg is patched with changes from inserted_1_B.gpkg (1 inserted feature), final state is modified_1_geom.gpkg + inserted_1_B.gpkg
    v10: nothing happened, just to ensure last diff is not last version of project file
    """
    geodiff = GeoDiff()
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    update_meta = _file_info(test_project_dir, 'base.gpkg')
    diff_meta_A = create_diff_meta('base.gpkg', 'inserted_1_A.gpkg', test_project_dir)
    diff_meta_mod = create_diff_meta('base.gpkg', 'modified_1_geom.gpkg', test_project_dir)
    rename_meta = {
        **_file_info(test_project_dir, 'base.gpkg'),
        'new_path': 'test.gpkg',
    }
    patch = os.path.join(TMP_DIR, 'patch')
    basefile = os.path.join(test_project_dir, 'base.gpkg')
    copy(basefile, patch)
    geodiff.apply_changeset(patch, os.path.join(TMP_DIR, diff_meta_mod['diff']['path']))
    diff_meta_B = create_diff_meta(patch, 'inserted_1_B.gpkg', test_project_dir)
    diff_meta_B['path'] = 'test.gpkg'

    # construct project versions
    changes = [
        {'added': [], 'removed': [_file_info(test_project_dir, 'base.gpkg')], 'renamed': [], 'updated': []},
        {'added': [_file_info(test_project_dir, 'base.gpkg')], 'removed': [], 'renamed': [], 'updated': []},
        {'added': [], 'removed': [], 'renamed': [], 'updated': [diff_meta_A]},
        {'added': [], 'removed': [], 'renamed': [], 'updated': [update_meta]},  # force update with full file
        {'added': [], 'removed': [], 'renamed': [], 'updated': [diff_meta_mod]},
        {'added': [], 'removed': [], 'renamed': [rename_meta], 'updated': []},  # file renamed, will be tracked with different name
        {'added': [], 'removed': [], 'renamed': [], 'updated': []},
        {'added': [], 'removed': [], 'renamed': [], 'updated': [diff_meta_B]},
        {'added': [], 'removed': [], 'renamed': [], 'updated': []},
    ]
    version_files = project.files
    for i, change in enumerate(changes):
        ver = 'v{}'.format(i + 2)
        if change['added']:
            meta = change['added'][0]
            meta['location'] = os.path.join(ver, meta['path'])
            new_file = os.path.join(project.storage.project_dir, meta['location'])
            os.makedirs(os.path.dirname(new_file), exist_ok=True)
            copy(os.path.join(test_project_dir, meta['path']), new_file)
            version_files.append(meta)
        elif change['updated']:
            meta = change['updated'][0]
            f_updated = next(f for f in version_files if f['path'] == meta['path'])
            new_location = os.path.join(ver, f_updated['path'])
            patchedfile = os.path.join(project.storage.project_dir, new_location)
            os.makedirs(os.path.dirname(patchedfile), exist_ok=True)
            if 'diff' in meta.keys():
                basefile = os.path.join(project.storage.project_dir, f_updated['location'])
                changefile = os.path.join(TMP_DIR, meta['diff']['path'])
                copy(basefile, patchedfile)
                geodiff.apply_changeset(patchedfile, changefile)
                meta['diff']['location'] = os.path.join(ver, meta['diff']['path'])
                move(changefile, os.path.join(project.storage.project_dir, meta['diff']['location']))
            else:
                copy(os.path.join(test_project_dir, f_updated['path']), patchedfile)
                f_updated.pop('diff', None)
            meta['location'] = new_location
            f_updated.update(meta)
        elif change['renamed']:
            f_renamed = next(f for f in version_files if f['path'] == change['renamed'][0]['path'])
            f_renamed['path'] = change['renamed'][0]['new_path']
        elif change['removed']:
            f_removed = next(f for f in version_files if f['path'] == change['removed'][0]['path'])
            version_files.remove(f_removed)
        else:
            pass

        pv = ProjectVersion(project, ver, project.creator.username, change, version_files, '127.0.0.1')
        db.session.add(pv)
        db.session.commit()
        version_files = pv.files
        assert pv.project_size == sum(file['size'] for file in version_files)

    project.files = version_files
    project.disk_usage = sum(file['size'] for file in project.files)
    project.tags = resolve_tags(version_files)
    project.latest_version = project.versions[0].name
    db.session.add(project)
    flag_modified(project, "files")
    db.session.commit()
    return project


@pytest.fixture(scope='function')
def test_organisation(client):
    """ Test organisation """
    user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    org = Organisation(name=TEST_ORG, creator_id=user.id)
    org_owner = add_user("owner", "owner")
    org.owners.append(org_owner.id)
    org_admin = add_user("admin", "admin")
    org.admins.extend([org_owner.id, org_admin.id])
    db.session.add(org)
    db.session.commit()
    # create a free organisation -> assign zero storage
    account = Account.query.filter_by(type="organisation", owner_id=org.id).first()
    account.namespace.storage = 0
    db.session.commit()
    return org
