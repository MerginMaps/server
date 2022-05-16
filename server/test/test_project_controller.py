# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import os
import pytest
import json
import uuid
import math
import time
import hashlib
import shutil
from datetime import datetime
from dateutil.tz import tzlocal
from pygeodiff import GeoDiff
from flask import url_for, current_app

from src import db
from src.models.db_models import (Project, Upload, ProjectVersion, ProjectAccess, ProjectTransfer,
                                  Namespace, Account, RemovedProject)
from src.models.schemas import ProjectSchema
from src.mergin_utils import generate_checksum, is_versioned_file, resolve_tags
from src.auth.models import User, UserProfile

from . import test_project, test_namespace, test_project_dir, json_headers, TMP_DIR
from .utils import add_user, create_project, DateTimeEncoder, initialize

CHUNK_SIZE = 1024


def test_file_history(client, diff_project):
    resp = client.get('/v1/resource/history/{}/{}?path={}'.format(test_namespace, test_project, 'test.gpkg'))
    history = resp.json['history']
    assert resp.status_code == 200
    assert 'v2' not in history
    assert 'v8' not in history
    assert history['v3']['change'] == 'added'
    assert history['v9']['change'] == 'updated'
    assert 'location' not in history['v9']
    assert 'expiration' in history['v9']

    resp = client.get('/v1/project/{}/{}?since=v1'.format(test_namespace, test_project))
    files = resp.json["files"]
    history = files[-1]["history"]
    assert files[-1]["path"] == 'test.gpkg'
    assert resp.status_code == 200
    assert 'v2' not in history
    assert 'v8' not in history
    assert history['v3']['change'] == 'added'
    assert history['v9']['change'] == 'updated'

    resp = client.get('/v1/project/{}/{}?since=v4'.format(test_namespace, test_project))
    files = resp.json["files"]
    history = files[-1]["history"]
    assert files[-1]["path"] == 'test.gpkg'
    assert resp.status_code == 200
    assert 'v3' not in history
    assert history['v9']['change'] == 'updated'

    # check geodiff changeset in project version object
    resp = client.get('/v1/project/version/{}/{}?version_id=v9'.format(test_namespace, test_project))
    version_info = resp.json[0]
    assert "changesets" in version_info
    # the only diff update in version v9 is test.gpkg
    assert len(version_info["changesets"].keys()) == 1
    assert "test.gpkg" in version_info["changesets"]
    assert "summary" in version_info["changesets"]["test.gpkg"]
    assert "size" in version_info["changesets"]["test.gpkg"]
    # test when no diffs were applied
    resp = client.get('/v1/project/version/{}/{}?version_id=v10'.format(test_namespace, test_project))
    assert not resp.json[0]["changesets"]

    # not geodiff file -> empty history
    resp = client.get('/v1/resource/history/{}/{}?path={}'.format(test_namespace, test_project, 'test_dir/test2.txt'))
    assert resp.status_code == 200
    assert not resp.json['history']

    # not existing file
    resp = client.get('/v1/resource/history/{}/{}?path={}'.format(test_namespace, test_project, 'not_existing.txt'))
    assert resp.status_code == 404

    # test to delete user and account with all of depended entries
    # user delete -> profile  + do account delete -> namespace -> project -> (version, upload, transfer, access)
    account = Account.query.filter_by(type="user", owner_id=1).first()
    db.session.delete(account)
    User.query.filter_by(username="mergin").delete()
    db.session.commit()
    project = Project.query.first()
    upload = Upload.query.first()
    ns = Namespace.query.first()
    assert not project
    assert not upload
    assert not ns


def test_get_projects(app):
    app.config['BEARER_TOKEN_EXPIRATION'] = 4
    client = app.test_client()
    response = client.post("/v1/auth/login", data=json.dumps({'login': 'mergin', 'password': 'ilovemergin'}),
                headers=json_headers)
    data = json.loads(response.data)
    session = data["session"]
    token = session["token"]
    resp = client.get('/v1/project')
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data)
    assert test_project in resp_data[0]["name"]
    time.sleep(5)
    url = '/v1/project?flag=created'
    resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_get_paginated_projects(client):
    user = User.query.filter_by(username="mergin").first()
    for i in range(14):
        create_project('foo' + str(i), test_namespace, user)

    resp = client.get('/v1/project/paginated?page=1&per_page=10&as_admin=true')
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 10
    assert resp_data.get("count") == 15
    assert "foo8" in resp_data.get("projects")[9]["name"]
    assert "v0" == resp_data.get("projects")[9]["version"]

    resp = client.get('/v1/project/paginated?page=1&per_page=10&order_params=updated_desc')
    resp_data = json.loads(resp.data)
    assert test_project in resp_data.get("projects")[0]["name"]

    resp = client.get('/v1/project/paginated?page=2&per_page=10&order_params=namespace_asc,updated_desc')
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 5
    assert resp_data.get("count") == 15
    assert "foo0" in resp_data.get("projects")[4]["name"]

    resp = client.get('/v1/project/paginated?page=1&per_page=10&order_params=updated_desc&namespace=foo1')
    resp_data = json.loads(resp.data)
    assert resp_data.get("count") == 0

    resp = client.get('/v1/project/paginated?page=1&per_page=10&name=foo1')
    resp_data = json.loads(resp.data)
    assert resp_data.get("count") == 5

    resp = client.get('/v1/project/paginated?page=1&per_page=101&name=foo1')
    assert resp.status_code == 400
    assert '101 is greater than the maximum of 100' in resp.json.get('detail')

    add_user('user2', 'ilovemergin')
    user2 = User.query.filter_by(username="user2").first()
    create_project('foo_a', 'user2', user2)

    resp = client.get('/v1/project/paginated?page=1&per_page=10&only_namespace=user2&as_admin=true')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp_data.get("projects")) == 1
    assert resp_data.get("count") == 1
    assert "foo_a" in resp_data.get("projects")[0]["name"]

    resp = client.get('/v1/project/paginated?page=1&per_page=10&only_namespace=user2')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp_data.get("projects")) == 0
    assert resp_data.get("count") == 0

    project = Project.query.filter(Project.name == "foo_a").first()
    readers = project.access.readers.copy()
    readers.append(user.id)
    project.access.readers = readers
    # flag_modified(project.access, "owners")
    db.session.commit()

    resp = client.get('/v1/project/paginated?page=1&per_page=10&only_namespace=user2')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp_data.get("projects")) == 1
    assert resp_data.get("count") == 1

    project = Project.query.filter(Project.name == "foo_a").first()
    readers = project.access.readers.copy()
    readers.remove(user.id)
    project.access.readers = readers
    project.access.public = True
    project.updated = datetime.utcnow()
    db.session.commit()

    resp = client.get('/v1/project/paginated?page=1&per_page=10&name=foo_a')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("projects")[0]["name"] == "foo_a"

    # searching also in namespace
    resp = client.get('/v1/project/paginated?page=1&per_page=10&name=user')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1

    resp = client.get('/v1/project/paginated?page=1&per_page=10&only_public=true')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 2

    resp = client.get('/v1/project/paginated?page=1&per_page=10&name=foo_a&public=false')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp_data.get("projects")) == 0

    resp = client.get('/v1/project/paginated?page=1&per_page=15&name=test')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert not resp_data.get("projects")[0].get("has_conflict")

    # tests if project contains conflict files
    project = Project.query.filter(Project.name == "test").first()
    files = project.files.copy()
    files.append({
        'checksum': '89469a6482267de394c7c7270cb7ffafe694ea76',
        'location': 'v1/base.gpkg_rebase_conflicts',
        'mtime': '2021-04-14T17:33:32.766731Z',
        'path': 'base.gpkg_rebase_conflicts',
        'size': 98304
    })
    project.files = files
    db.session.commit()

    resp = client.get('/v1/project/paginated?page=1&per_page=15&name=test')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert resp_data.get("projects")[0].get("has_conflict")

    files = project.files.copy()
    files.remove([f for f in files if f.get('path') == 'base.gpkg'][0])
    project.files = files
    db.session.commit()

    resp = client.get('/v1/project/paginated?page=1&per_page=15&name=test')
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert not resp_data.get("projects")[0].get("has_conflict")


def test_get_projects_by_names(client):
    user = User.query.filter_by(username="mergin").first()
    create_project('foo', test_namespace, user)
    add_user('user2', 'ilovemergin')
    user2 = User.query.filter_by(username="user2").first()
    create_project('foo', 'user2', user2)
    create_project('other', 'user2', user2)

    data = {"projects": [
        "mergin/foo",
        "user2/foo",
        "user2/other",
        "something"
    ]}
    resp = client.post('/v1/project/by_names', data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert resp_data.get("mergin/foo").get("name") == "foo"
    assert resp_data.get("user2/foo").get("error") == 403
    assert resp_data.get("user2/other").get("error") == 403
    assert resp_data.get("something").get("error") == 404


add_project_data = [
    ({"name": ' foo ', "template": test_project}, 200),  # valid project name, whitespace will be removed
    ({"name": 'foo/bar', "template": test_project}, 400),  # invalid project name
    ({"name": 'ba%r', "template": test_project}, 400),  # invalid project name
    ({"name": 'bar*', "template": test_project}, 200),  # valid project name
    ({"name": test_project}, 409),
]


@pytest.mark.parametrize("data,expected", add_project_data)
def test_add_project(client, app, data, expected):
    # add TEMPLATES user and make him creator of test_project (to become template)
    user = User(username='TEMPLATES', passwd='templates', is_admin=False, email='templates@mergin.com')
    user.active = True
    db.session.add(user)
    template = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    template.creator = user
    db.session.commit()

    resp = client.post('/v1/project/{}'.format(test_namespace), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        project = Project.query.filter_by(name=data['name'].strip(), namespace=test_namespace).first()
        assert not any(x['checksum'] != y['checksum'] and x['path'] != y['path'] for x, y in zip(project.files, template.files))
        assert project.versions[0].user_agent is not None
        shutil.rmtree(os.path.join(app.config['LOCAL_PROJECTS'], project.storage.project_dir)) # cleanup


def test_versioning(client):
    # test if blank project has version set up to v0
    resp = client.post('/v1/project/{}'.format(test_namespace), data=json.dumps({"name": "version_test"}), headers=json_headers)
    assert resp.status_code == 200
    project = Project.query.filter_by(name="version_test", namespace=test_namespace).first()
    assert project.versions[0].name == "v0"
    assert project.versions[0].project_size == 0

    # testing if versions related to same project name and different namespace is not deleted
    user = User(username='version', passwd='version', is_admin=True, email='version@mergin.com')
    user.active = True
    db.session.add(user)
    db.session.commit()
    client.get(url_for('auth.logout'))
    client.post(url_for('auth.login'), data=json.dumps({'login': "version", 'password': 'version'}),
                headers=json_headers)

    resp = client.post('/v1/project/{}'.format("version"), data=json.dumps({"name": "version_test"}),
                       headers=json_headers)
    client.delete('/v1/project/{}/{}'.format("version", "version_test"))
    assert resp.status_code == 200
    project = Project.query.filter_by(name="version_test", namespace=test_namespace).first()
    assert len(project.versions) == 1


def test_delete_project(client):
    project = Project.query.filter_by(namespace=test_namespace, name=test_project).first()
    creator_id = project.creator_id
    files = project.files
    changes = project.versions[0].changes
    project_dir = project.storage.project_dir
    assert os.path.exists(project_dir)
    assert not RemovedProject.query.filter_by(namespace=test_namespace, name=test_project).count()
    resp = client.delete('/v1/project/{}/{}'.format(test_namespace, test_project))
    assert resp.status_code == 200
    assert not Project.query.filter_by(namespace=test_namespace, name=test_project).count()
    rp = RemovedProject.query.filter_by(namespace=test_namespace, name=test_project).first()
    assert rp.properties["creator_id"] == creator_id
    assert rp.properties["files"] == files
    assert rp.properties["versions"][0]["changes"] == changes
    assert os.path.exists(project_dir)  # files not deleted yet, since there is possibility of restore

    # do permanent delete by removing backup
    resp = client.delete(url_for('retire_removed_project', id=rp.id))
    assert resp.status_code == 204
    assert not RemovedProject.query.filter_by(namespace=test_namespace, name=test_project).count()
    assert not os.path.exists(project_dir)


def test_restore_project(client):
    project = Project.query.filter_by(namespace=test_namespace, name=test_project).first()
    creator_id = project.creator_id
    files = project.files
    changes = project.versions[0].changes
    project_dir = project.storage.project_dir
    project_info = ProjectSchema(exclude=("permissions", "access", )).dump(project)
    client.delete(f"/v1/project/{test_namespace}/{test_project}")

    # test listing
    resp = client.get(url_for("paginate_removed_projects"))
    assert resp.json["count"] == 1
    rp = resp.json["projects"][0]
    resp = client.post(url_for("restore_project", id=rp["id"]))
    assert resp.status_code == 201

    restored_project = Project.query.filter_by(namespace=test_namespace, name=test_project).first()
    assert restored_project.creator_id == creator_id
    assert restored_project.files == files
    assert restored_project.versions[0].changes == changes
    assert restored_project.access.owners[0] == creator_id
    assert os.path.exists(project_dir)
    assert ProjectSchema(exclude=("permissions", "access", )).dump(restored_project) == project_info


test_project_data = [
    ({"storage_params": {"type": "local", "location": "some_test"}, "name": test_project}, 200),
    ({"storage_params": {"type": "local", "location": 'foo'}, "name": 'bar'}, 404),
]


@pytest.mark.parametrize("data,expected", test_project_data)
def test_get_project(client, data, expected):
    resp = client.get('/v1/project/{}/{}'.format(test_namespace, data["name"]))
    assert resp.status_code == expected
    if expected == 200:
        resp_data = json.loads(resp.data)
        assert test_project in resp_data["name"]
        assert len(resp_data["access"]["owners"])
        owner = User.query.get(resp_data["access"]["owners"][0])
        assert resp_data["access"]["ownersnames"][0] == owner.username


test_history_data = [
    ('v9', {'basefile': {}, 'versions': ['v9']}),
    ('v5', {'basefile': {}, 'versions': ['v9', 'v7', 'v6', 'v5']}),
    ('v4', {'basefile': {'path': 'base.gpkg', 'version': 'v5'}, 'versions': ['v9', 'v7', 'v6', 'v5', 'v4']}),
    ('v1', {'basefile': {'path': 'base.gpkg', 'version': 'v5'}, 'versions': ['v9', 'v7', 'v6', 'v5', 'v4', 'v3']})  # after remove we can't go any further in history
]


@pytest.mark.parametrize("version,expected", test_history_data)
def test_get_project_with_history(client, diff_project, version, expected):
    resp = client.get('/v1/project/{}/{}?since={}'.format(test_namespace, test_project, version))
    assert resp.status_code == 200
    history = next(item['history'] for item in resp.json['files'] if item['path'] == 'test.gpkg')
    assert set(expected['versions']) == set(history.keys())
    if expected['basefile']:
        ver = expected['basefile']['version']
        assert history[ver]['path'] == expected['basefile']['path']
        assert 'diff' not in history[ver]


def test_get_project_at_version(client, diff_project):
    resp = client.get(f'/v1/project/{test_namespace}/{test_project}')
    latest_project = resp.json
    version = 'v5'
    resp2 = client.get(f'/v1/project/{test_namespace}/{test_project}?version={version}')
    info = resp2.json
    # check version non-specific data
    for key in ['created', 'creator', 'uploads', 'name', 'namespace', 'access', 'permissions']:
        assert info[key] == latest_project[key]
    assert info['version'] == version
    version_obj = next(v for v in diff_project.versions if v.name == version)
    assert len(info['files']) == len(version_obj.files)
    assert info['updated'] == version_obj.created.strftime('%Y-%m-%dT%H:%M:%S%zZ')
    assert info['tags'] == ['valid_qgis', 'input_use']
    assert info['disk_usage'] == sum(f["size"] for f in version_obj.files)

    # compare with most recent version
    version = 'v10'
    resp3 = client.get(f'/v1/project/{test_namespace}/{test_project}?version={version}')
    for key, value in latest_project.items():
        # skip updated column as that one would differ slightly due to delay between project and version object update
        if key == 'updated' or key == 'access_requests' or 'latest_version':
            continue
        assert value == resp3.json[key]

    resp4 = client.get(f'/v1/project/{test_namespace}/{test_project}?version=v100')
    assert resp4.status_code == 404

    resp5 = client.get(f'/v1/project/{test_namespace}/{test_project}?version=v1&since=v1')
    assert resp5.status_code == 400


def test_update_project(client):
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    # need for private project
    project.access.public = False
    db.session.add(project)
    # add some tester
    test_user = User(username='tester', passwd='tester', is_admin=False, email='tester@mergin.com')
    test_user.active = True
    test_user.profile = UserProfile()
    db.session.add(test_user)
    db.session.commit()

    # add test user as reader to project
    data = {"access": {"readers": project.access.readers + [test_user.id]}}
    resp = client.put('/v1/project/{}/{}'.format(test_namespace, test_project), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 200
    assert test_user.id in project.access.readers

    # try to remove project creator from owners
    data = {"access": {"owners": [test_user.id]}}
    resp = client.put('/v1/project/{}/{}'.format(test_namespace, test_project), data=json.dumps(data), headers=json_headers)
    assert resp.status_code == 400


test_download_proj_data = [
    (test_project, None, 200, None),
    (test_project, "zip", 200, None),
    (test_project, "foo", 400, None),
    ('bar', None, 404, None),
    (test_project, None, 200, 'v1'),
    (test_project, "zip", 200, 'v1'),
    (test_project, "foo", 400, 'v1'),
    ('bar', None, 404, 'v99'),
    (test_project, None, 404, 'v100'),
    (test_project, "zip", 404, 'v100'),
    (test_project, "foo", 400, 'v100'),
    ('bar', None, 404, 'v100')
]


@pytest.mark.parametrize("proj_name,out_format,expected,version", test_download_proj_data)
def test_download_project(client, proj_name, out_format, expected, version):
    if out_format:
        resp = client.get('/v1/project/download/{}/{}?{}format={}'.format(
            test_namespace, proj_name,
            'version={}&'.format(version) if version else '',
            out_format
        ))
        if expected == 200:
            header = 'attachment; filename={}{}.zip'.format(
                proj_name, '-' + version if version else '')
            assert header in resp.headers[1][1]
    else:
        resp = client.get('/v1/project/download/{}/{}{}'.format(
            test_namespace, proj_name,
            '?version={}'.format(version) if version else ''))
        if expected == 200:
            assert 'multipart/form-data' in resp.headers[0][1]

    assert resp.status_code == expected


test_download_file_data = [
    (test_project, 'test.txt', 'text/plain', 200),
    (test_project, 'logo.pdf', 'application/pdf', 200),
    (test_project, 'logo.jpeg', 'image/jpeg', 200),
    (test_project, 'base.gpkg', 'None', 200),
    (test_project, 'json.json', 'text/plain', 200),
    (test_project, 'foo.txt', None, 404),
    ('bar', 'test.txt', None, 404)
]


@pytest.mark.parametrize("proj_name,file_path,mimetype,expected", test_download_file_data)
def test_download_file(client, proj_name, file_path, mimetype, expected):
    resp = client.get('/v1/project/raw/{}/{}?file={}'.format(test_namespace, proj_name, file_path))
    assert resp.status_code == expected
    if resp.status_code == 200:
        assert resp.headers["content-type"] == mimetype


test_download_file_version_data = [
    (test_project, 'v8', 'base.gpkg', 404),  # version does not has base.gpkg (but test.gpkg)
    (test_project, 'v8', 'test.gpkg', 200),  # version has test.gpkg because renamed but nothing uploaded
    (test_project, 'v9', 'test.gpkg', 200),  # actual changed happened (update with diff)
    (test_project, 'v10', 'test.gpkg', 200),  # again, file as not changed
    (test_project, 'v1', 'test.txt', 200),  # initial file (ordinary text file)
    (test_project, 'v10', 'test.txt', 200),  # unmodified file (ordinary text file)
]


@pytest.mark.parametrize("proj_name,version,file_path,expected", test_download_file_version_data)
def test_download_file_by_version(client, diff_project, proj_name, version, file_path, expected):
    project = diff_project

    project_version = next((v for v in project.versions if v.name == version), None)
    for file in project_version.files:
        if not is_versioned_file(file['path']):
            continue

        # let's delete the file, so it can be restored
        if file['path'] == file_path:
            file_location = os.path.join(project.storage.project_dir, file['location'])
            os.remove(file_location)

    # download whole files, no diffs
    resp = client.get('/v1/project/raw/{}/{}?file={}&version={}'.format(test_namespace, proj_name, file_path, version))
    assert resp.status_code == expected

test_download_file_diffs_data = [
    (test_project, '', 'base.gpkg', 400),  # no version specified
    (test_project, 'v3', 'base.gpkg', 404),  # upload
    (test_project, 'v4', 'base.gpkg', 200),  # update with diff
    (test_project, 'v5', 'base.gpkg', 404),  # forced update without diff
    (test_project, 'v10', 'test.gpkg', 404),  # nothing changed
    (test_project, 'v1', 'test.txt', 404),  # ordinary text file
]

@pytest.mark.parametrize("proj_name,version,file_path,expected", test_download_file_diffs_data)
def test_download_file_version_diffs(client, diff_project, proj_name, version, file_path, expected):
    # download only diffs
    resp = client.get(f'/v1/project/raw/{test_namespace}/{proj_name}?file={file_path}&version={version}&diff=True')
    assert resp.status_code == expected


def test_download_diff_file(client, diff_project):
    test_file = 'base.gpkg'
    # download version of file with force update (no diff)
    resp = client.get('/v1/project/raw/{}/{}?file={}&diff=true&version=v5'.format(test_namespace, test_project, test_file))
    assert resp.status_code == 404

    # updated with diff based on 'inserted_1_A.gpkg'
    pv_2 = next((v for v in diff_project.versions if v.name == 'v4'), None)
    file_meta = pv_2.changes['updated'][0]
    resp = client.get('/v1/project/raw/{}/{}?file={}&diff=true&version=v4'.format(test_namespace, test_project, test_file))
    assert resp.status_code == 200
    # check we get the same file with diff that we created (uploaded)
    downloaded_file = os.path.join(TMP_DIR, 'download' + str(uuid.uuid4()))
    with open(downloaded_file, 'wb') as f:
        f.write(resp.data)
    assert file_meta['diff']['checksum'] == generate_checksum(downloaded_file)
    patched_file = os.path.join(TMP_DIR, 'patched' + str(uuid.uuid4()))
    geodiff = GeoDiff()
    basefile = os.path.join(test_project_dir, test_file)
    shutil.copy(basefile, patched_file)
    geodiff.apply_changeset(patched_file, downloaded_file)
    changes = os.path.join(TMP_DIR, 'changeset' + str(uuid.uuid4()))
    geodiff.create_changeset(patched_file, os.path.join(test_project_dir, 'inserted_1_A.gpkg'), changes)
    assert not geodiff.has_changes(changes)

    # download full version after file was removed
    os.remove(os.path.join(diff_project.storage.project_dir, file_meta['location']))
    resp = client.get('/v1/project/raw/{}/{}?file={}&version=v4'.format(test_namespace, test_project, test_file))
    assert resp.status_code == 200


def test_download_fail(app, client):
    # remove project files to mimic mismatch with db
    os.remove(os.path.join(app.config['LOCAL_PROJECTS'], test_namespace, test_project, 'v1', 'test.txt'))
    resp = client.get('/v1/project/raw/{}/{}?file={}'.format(test_namespace, test_project, 'test.txt'))
    assert resp.status_code == 404

    shutil.rmtree(os.path.join(app.config['LOCAL_PROJECTS'], test_namespace, test_project))

    resp = client.get('/v1/project/download/{}/{}'.format(test_namespace, test_project))
    assert resp.status_code == 404

    resp = client.get('/v1/project/raw/{}/{}?file={}'.format(test_namespace, test_project, 'test.txt'))
    assert resp.status_code == 404

    p = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    db.session.delete(p)
    db.session.commit()
    resp = client.get('/v1/project/raw/{}/{}?file={}'.format(test_namespace, test_project, 'test.txt'))
    assert resp.status_code == 404


def _file_info(project_dir, path):
    abs_path = os.path.join(project_dir, path)
    f_size = os.path.getsize(abs_path)
    return {
        "path": path,
        "checksum": generate_checksum(abs_path),
        "size": f_size,
        "mtime": datetime.fromtimestamp(os.path.getmtime(abs_path), tzlocal()),
        "chunks": [str(uuid.uuid4()) for i in range(math.ceil(f_size / CHUNK_SIZE))],
    }


def create_diff_meta(base, modified, project_dir):
    """Create diff metadata for updating files."""
    geodiff = GeoDiff()
    diff_id = str(uuid.uuid4())
    diff_name = base + '-diff-' + diff_id
    basefile = os.path.join(project_dir, base)
    modfile = os.path.join(project_dir, modified)
    changeset = os.path.join(TMP_DIR, diff_name)
    geodiff.create_changeset(basefile, modfile, changeset)

    diff_meta = {
        **_file_info(project_dir, base),
        "chunks": [str(uuid.uuid4()) for i in range(math.ceil(_file_info(TMP_DIR, diff_name)["size"] / CHUNK_SIZE))],
        "diff": {
            "path": diff_name,
            "checksum": generate_checksum(changeset),
            "size": os.path.getsize(changeset)
        }
    }
    diff_meta["path"] = base
    return diff_meta


def _get_changes(project_dir, diff=False):
    changes = {
        "added": [
            {
                **_file_info(project_dir, "test_dir/test4.txt"),
                "chunks": [str(uuid.uuid4()) for i in range(math.ceil(_file_info(project_dir, "test_dir/test4.txt")["size"] / CHUNK_SIZE))]
            }
        ],
        "renamed": [
            {
                **_file_info(project_dir, "test_dir/test2.txt"),
                "new_path": "test_dir/renamed.txt",
            }
        ],
        "updated": [
            {
                **_file_info(project_dir, "test.txt"),
                "chunks": [str(uuid.uuid4()) for i in
                           range(math.ceil(_file_info(project_dir, "test.txt")["size"] / CHUNK_SIZE))]
            }
        ],
        "removed": [
            _file_info(project_dir, "test3.txt")
        ]
    }
    return changes


def _get_changes_without_added(project_dir):
    changes = _get_changes(project_dir)
    changes["added"] = []
    return changes


def _get_changes_without_mtime(project_dir):
    changes = _get_changes_without_added(project_dir)
    del changes['updated'][0]['mtime']
    return changes


def _get_changes_with_broken_mtime(project_dir):
    changes = _get_changes_without_added(project_dir)
    changes["renamed"] = []
    changes["removed"] = []
    changes['updated'][0]['mtime'] = "frfr"
    return changes


def _get_changes_with_diff(project_dir):
    changes = _get_changes_without_added(project_dir)
    # add some updates using diff file
    diff_meta = create_diff_meta('base.gpkg', 'inserted_1_A.gpkg', project_dir)
    changes['updated'].append(diff_meta)
    return changes

test_push_data = [
    ({'version': 'v1', 'changes': _get_changes_without_added(test_project_dir)}, 200),  # success
    ({'version': 'v1', 'changes': _get_changes_with_diff(test_project_dir)}, 200),  # with diff, success
    ({'version': 'v1', 'changes': _get_changes(test_project_dir)}, 400),  # contains already uploaded file
    ({'version': 'v0', 'changes': _get_changes_without_added(test_project_dir)}, 400),  # version mismatch
    ({'version': 'v1', 'changes': {}}, 400),  # wrong changes format
    ({'version': 'v1', 'changes': {'added': [], 'removed': [], 'updated': [], 'renamed': []}}, 400),  # no changes requested
    ({'version': 'v1', 'changes': {'added': [{'path': 'test.txt'}], 'removed': [], 'updated': [{'path': 'test.txt'}], 'renamed': []}}, 400),  # inconsistent changes
    ({'changes': _get_changes_without_added(test_project_dir)}, 400)  # missing version (required parameter)
]


@pytest.mark.parametrize("data,expected", test_push_data)
def test_push_project_start(client, data, expected):
    url = '/v1/project/push/{}/{}'.format(test_namespace, test_project)
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        assert 'transaction' in resp.json.keys()


def test_push_to_new_project(client):
    # create blank project
    p = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    project = Project('blank', p.storage_params, p.creator, p.namespace, files=[])
    db.session.add(project)
    pa = ProjectAccess(project, True)
    db.session.add(pa)
    db.session.commit()

    current_app.config['BLACKLIST'] = ["test4"]
    url = '/v1/project/push/{}/{}'.format(test_namespace, 'blank')
    data = {'version': 'v0', 'changes': _get_changes(test_project_dir)}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 200

    upload_id = resp.json['transaction']
    upload = Upload.query.filter_by(id=upload_id).first()
    blacklisted_file = all(added['path'] != 'test_dir/test4.txt' for added in upload.changes['added'])
    assert blacklisted_file

    data = {'version': 'v1', 'changes': _get_changes(test_project_dir)}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 400

    data = {'version': 'v100', 'changes': _get_changes(test_project_dir)}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'First push should be with v0'


def test_sync_no_upload(client):
    # test project sync that does not require data upload (e.g. renaming)
    url = '/v1/project/push/{}/{}'.format(test_namespace, test_project)
    changes = _get_changes(test_project_dir)
    changes['added'] = changes['removed'] = changes['updated'] = []
    data = {'version': 'v1', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    renamed = next((i for i in project.files if i['path'] == 'test_dir/renamed.txt'), None)
    assert resp.status_code == 200
    assert renamed is not None
    assert not project.uploads.all()

    # check project version update after successful sync
    resp_2 = client.get('/v1/project/version/{}/{}'.format(test_namespace, test_project))
    assert resp_2.status_code == 200
    assert len(resp_2.json) == 2
    assert resp_2.json[0]['name'] == 'v2'
    assert resp_2.json[0]['author'] == 'mergin'
    assert resp_2.json[0]['changes']['renamed'][0]['new_path'] == changes['renamed'][0]['new_path']


def test_push_integrity_error(client, app):
    app.config['LOCKFILE_EXPIRATION'] = 5
    url = '/v1/project/push/{}/{}'.format(test_namespace, test_project)
    changes = _get_changes_without_added(test_project_dir)
    data = {'version': 'v1', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 200

    # try another request for transaction
    resp2 = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp2.status_code == 400
    assert resp2.json['detail'] == 'Another process is running. Please try later.'

    # try immediate project sync without transaction (no upload)
    changes['added'] = changes['removed'] = changes['updated'] = []
    data = {'version': 'v1', 'changes': changes}
    resp3 = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp3.status_code == 400

    time.sleep(5)
    # try another request for transaction
    resp4 = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp4.status_code == 200


def test_exceed_data_limit(client):
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    user_disk_space = sum(p.disk_usage for p in project.creator.projects)
    ns = Namespace.query.filter_by(name=project.creator.username).first()
    # set basic storage that it is fully used
    ns.storage = user_disk_space
    db.session.add(ns)
    db.session.commit()

    url = '/v1/project/push/{}/{}'.format(test_namespace, test_project)
    changes = _get_changes(test_project_dir)
    changes['renamed'] = changes['removed'] = changes['updated'] = []
    changes["added"][0]["path"] = "xxx.txt"
    data = {'version': 'v1', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'You have reached a data limit'

    # try to make some space only by removing file
    changes["added"] = []
    changes["removed"] = [project.files[0]]
    data = {'version': 'v1', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 200

    # tight limit again
    ns.storage = sum(p.disk_usage for p in project.creator.projects)
    db.session.commit()

    changes['renamed'] = changes['removed'] = changes['updated'] = []
    changes['added'] = [{
        **_file_info(test_project_dir, "test_dir/test2.txt"),
        "chunks": [str(uuid.uuid4()) for i in range(math.ceil(_file_info(test_project_dir, "test_dir/test2.txt")["size"] / CHUNK_SIZE))]
    }]
    changes["added"][0]["path"] = "xxx.txt"
    data = {'version': 'v2', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'You have reached a data limit'

    # try to upload while removing some other files, test4.txt being larger than test2.txt
    changes["removed"] = [{**_file_info(test_project_dir, "test_dir/test4.txt")}]
    data = {'version': 'v2', 'changes': changes}
    resp = client.post(url, data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)
    assert resp.status_code == 200


def create_transaction(username, changes, version=1):
    """Create transaction in mergin/test project for update to particular version by specified user."""
    user = User.query.filter_by(username=username).first()
    project = Project.query.filter_by(name=test_project, namespace='mergin').first()
    upload = Upload(project, version, changes, user.id)
    db.session.add(upload)
    db.session.commit()
    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", upload.id)
    os.makedirs(upload_dir)
    open(os.path.join(upload_dir, 'lockfile'), 'w').close()
    return upload, upload_dir


def remove_transaction(transaction_id):
    """Remove transaction from db and related files, use to clean after upload failure."""
    upload = Upload.query.get(transaction_id)
    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", transaction_id)
    db.session.delete(upload)
    db.session.commit()
    shutil.rmtree(upload_dir, ignore_errors=True)


def test_chunk_upload(client, app):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction('mergin', changes)
    chunk_id = upload.changes['added'][0]['chunks'][0]
    url = '/v1/project/push/chunk/{}/{}'.format(upload.id, chunk_id)
    with open(os.path.join(test_project_dir, 'test_dir', 'test4.txt'), 'rb') as file:
        data = file.read(CHUNK_SIZE)
        checksum = hashlib.sha1()
        checksum.update(data)
    headers = {"Content-Type": "application/octet-stream"}
    resp = client.post(url, data=data, headers=headers)
    assert resp.status_code == 200
    assert resp.json['checksum'] == checksum.hexdigest()

    # test to send bigger chunk than allowed
    app.config['MAX_CHUNK_SIZE'] = 10 * CHUNK_SIZE
    with open(os.path.join(test_project_dir, 'test_dir', 'test4.txt'), 'rb') as file:
        data = file.read(11 * CHUNK_SIZE)
    headers = {"Content-Type": "application/octet-stream"}
    resp = client.post(url, data=data, headers=headers)
    assert resp.status_code == 400
    assert resp.json['detail'] == 'Too big chunk'

    # test with transaction with no uploads expected
    changes = _get_changes(test_project_dir)
    changes['added'] = changes['removed'] = changes['updated'] = []
    upload.changes = changes
    db.session.add(upload)
    db.session.commit()
    resp2 = client.post(url, data=data, headers=headers)
    assert resp2.status_code == 404

    # cleanup
    shutil.rmtree(upload_dir)


def upload_chunks(upload_dir, changes):
    """Mimic chunks for upload to finish were already uploaded."""
    os.makedirs(os.path.join(upload_dir, 'chunks'))
    for f in changes['added'] + changes['updated']:
        source = os.path.join(TMP_DIR, f["diff"]["path"]) if "diff" in f else os.path.join(test_project_dir, f["path"])
        with open(source, 'rb') as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, 'chunks', chunk), 'wb') as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))


def test_push_finish(client):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction('mergin', changes)
    url = '/v1/project/push/finish/{}'.format(upload.id)

    resp = client.post(url)
    assert resp.status_code == 422
    assert 'corrupted_files' in resp.json['detail'].keys()
    assert not os.path.exists(os.path.join(upload_dir, "files", "test.txt"))

    os.mkdir(os.path.join(upload.project.storage.project_dir, 'v2'))
    # mimic chunks were uploaded
    os.makedirs(os.path.join(upload_dir, 'chunks'))
    for f in upload.changes['added'] + upload.changes['updated']:
        with open(os.path.join(test_project_dir, f["path"]), 'rb') as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, 'chunks', chunk), 'wb') as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))

    resp2 = client.post(url)
    assert resp2.status_code == 200
    assert not os.path.exists(upload_dir)
    assert upload.project.versions[0].user_agent is not None

    # test basic failures
    resp3 = client.post('/v1/project/push/finish/not-existing')
    assert resp3.status_code == 404

    # create new user with permission to do uploads
    user = User(username='tester', passwd='test', is_admin=False, email='tester@mergin.com')
    user.active = True
    db.session.add(user)
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    project.access.owners.append(user.id)
    db.session.commit()

    upload, upload_dir = create_transaction(user.username, changes)
    url = '/v1/project/push/finish/{}'.format(upload.id)
    db.session.add(upload)
    db.session.commit()
    # still log in as mergin user
    resp4 = client.post(url)
    assert resp4.status_code == 403


def test_push_close(client):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction('mergin', changes)
    url = '/v1/project/push/cancel/{}'.format(upload.id)
    resp = client.post(url)
    assert resp.status_code == 200


def test_whole_push_process(client):
    """ Test whole transactional upload from start, through uploading chunks to finish.
    Uploaded files contains also non-ascii chars to test.
    """
    test_dir = os.path.join(TMP_DIR, 'test_uploaded_files')
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    uploaded_files = ['テスト.txt', '£¥§.txt', 'name_1_1.txt', 'name\\1\\1.txt']
    # prepare dummy files
    os.mkdir(test_dir)
    for file in uploaded_files:
        with open(os.path.join(test_dir, file), 'w') as f:
            f.write("Hello Mergin")

    # push start: create upload transaction
    changes = {
        "added": [_file_info(test_dir, filename) for filename in uploaded_files],
        "renamed": [],
        "updated": [],
        "removed": []
    }
    resp = client.post(f'/v1/project/push/{test_namespace}/{test_project}', data=json.dumps({
        'version': 'v1',
        'changes': changes
    }, cls=DateTimeEncoder).encode("utf-8"), headers=json_headers)

    assert resp.status_code == 200
    assert 'transaction' in resp.json.keys()
    upload = Upload.query.get(resp.json['transaction'])
    assert upload

    # push upload: upload file chunks
    for file in changes["added"]:
        for chunk_id in file["chunks"]:
            url = '/v1/project/push/chunk/{}/{}'.format(upload.id, chunk_id)
            with open(os.path.join(test_dir, file['path']), 'rb') as f:
                data = f.read(CHUNK_SIZE)
                checksum = hashlib.sha1()
                checksum.update(data)
            resp = client.post(url, data=data, headers={"Content-Type": "application/octet-stream"})
            assert resp.status_code == 200
            assert resp.json['checksum'] == checksum.hexdigest()

    # push finish: call server to concatenate chunks and finish upload
    resp = client.post(f'/v1/project/push/finish/{upload.id}')
    assert resp.status_code == 200
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    for file in project.files:
        if file['path'] not in uploaded_files:
            continue
        file_location = os.path.join(project.storage.project_dir, file['location'])
        file_before_upload = os.path.join(test_dir, file['path'])
        assert os.path.exists(file_location)
        assert open(file_before_upload, 'r').read() == open(file_location, 'r').read()


def test_push_diff_finish(client):
    # success
    changes = _get_changes_with_diff(test_project_dir)
    upload, upload_dir = create_transaction('mergin', changes)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post('/v1/project/push/finish/{}'.format(upload.id))
    assert resp.status_code == 200
    # check there are not any changes between local modified file and server patched file (using geodiff)
    geodiff = GeoDiff()
    changeset = os.path.join(TMP_DIR, 'test_changeset')
    modfile = os.path.join(test_project_dir, 'inserted_1_A.gpkg')
    patchedfile = os.path.join(upload.project.storage.project_dir, 'v2', 'base.gpkg')
    geodiff.create_changeset(patchedfile, modfile, changeset)
    assert not geodiff.has_changes(changeset)
    os.remove(changeset)

    # try with valid update metadata but with conflicting diff (rebase was not done)
    upload, upload_dir = create_transaction('mergin', changes, 2)
    upload_chunks(upload_dir, upload.changes)

    resp = client.post('/v1/project/push/finish/{}'.format(upload.id))
    assert resp.status_code == 422
    assert 'base.gpkg error=project: mergin/test, geodiff error' in resp.json['detail']


clone_project_data = [
    ({"project": " clone "}, 'mergin', 200),  # clone own project
    ({}, 'mergin', 409),  # fail to clone own project into the same one
    ({"namespace": "foo"}, 'foo', 200),  # public project cloned by another user
    ({"namespace": "foo"}, 'foo', 403),  # fail to clone private project with no permissions granted
]


@pytest.mark.parametrize("data,username,expected", clone_project_data)
def test_clone_project(client, data, username, expected):
    endpoint = '/v1/project/clone/{}/{}'.format(test_namespace, test_project)
    # need for private project
    if expected == 403:
        p = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
        p.access.public = False
        db.session.add(p)
        db.session.commit()
    # add some user to test clone across namespaces
    if username != 'mergin':
        user = add_user(username, 'bar')
        # switch default user
        client.get(url_for('auth.logout'))
        client.post(url_for('auth.login'), data=json.dumps({'login': user.username, 'password': 'bar'}), headers=json_headers)

    resp = client.post(endpoint, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 200:
        ns = data.get('namespace', test_namespace)
        proj = data.get('project', test_project).strip()
        template = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
        project = Project.query.filter_by(name=proj, namespace=ns).first()
        assert not any(x['checksum'] != y['checksum'] and x['path'] != y['path'] for x, y in zip(project.files, template.files))
        assert os.path.exists(os.path.join(project.storage.project_dir, project.files[0]['location']))
        assert not project.access.public
        # cleanup
        shutil.rmtree(project.storage.project_dir)


def test_optimize_storage(app, diff_project):
    file_v2_base = os.path.join(diff_project.storage.project_dir, 'v4', 'base.gpkg')
    file_v4_base = os.path.join(diff_project.storage.project_dir, 'v6', 'base.gpkg')
    basefile_v1 = os.path.join(diff_project.storage.project_dir, 'v3', 'base.gpkg')
    basefile_v3 = os.path.join(diff_project.storage.project_dir, 'v5', 'base.gpkg')
    latest = os.path.join(diff_project.storage.project_dir, 'v9', 'test.gpkg')

    diff_project.storage.optimize_storage()
    # nothing removed since created recently
    assert os.path.exists(file_v2_base) and os.path.exists(file_v4_base)

    app.config['FILE_EXPIRATION'] = 0
    diff_project.storage.optimize_storage()
    assert not (os.path.exists(file_v2_base) and os.path.exists(file_v4_base))
    # we keep latest file, basefiles must stay (either very first one, or any other with forced update)
    assert os.path.exists(latest) and os.path.exists(basefile_v1) and os.path.exists(basefile_v3)

    # try again, nothing expected if files already removed
    diff_project.storage.optimize_storage()
    assert not os.path.exists(file_v2_base)


def test_version_file_restore(diff_project):
    test_file = os.path.join(diff_project.storage.project_dir, 'v4', 'base.gpkg')
    os.remove(test_file)
    diff_project.storage.restore_versioned_file('base.gpkg', 'v4')
    assert os.path.exists(test_file)

    # we can restore latest version (composed from multiple diffs)
    test_file = os.path.join(diff_project.storage.project_dir, 'v9', 'test.gpkg')
    os.remove(test_file)
    diff_project.storage.restore_versioned_file('test.gpkg', 'v9')
    assert os.path.exists(test_file)

    # basefile can not be restored
    test_file = os.path.join(diff_project.storage.project_dir, 'v5', 'base.gpkg')
    os.remove(test_file)
    diff_project.storage.restore_versioned_file('base.gpkg', 'v5')
    assert not os.path.exists(test_file)

    # no geodiff file can not be restored
    test_file = os.path.join(diff_project.storage.project_dir, 'v1', 'test.txt')
    os.remove(test_file)
    diff_project.storage.restore_versioned_file('test.txt', 'v1')
    assert not os.path.exists(test_file)


changeset_data = [
    ('v1', 'test.gpkg', 404),
    ('v1', 'test.txt', 404),
    ('v9', 'test.gpkg', 200),  # diff update in v9 version
    ('v10', 'test.gpkg', 404),  # no change of the file in v10 version
]


@pytest.mark.parametrize("version, path, expected", changeset_data)
def test_changeset_file(client, diff_project, version, path, expected):
    url = '/v1/resource/changesets/{}/{}/{}?path={}'.format(
        test_namespace, test_project, version, path)
    resp = client.get(url)
    assert resp.status_code == expected

    if resp.status_code == 200:
        version = ProjectVersion.query.filter_by(project_id=diff_project.id, name=version).first()
        file = next((f for f in version.files if f['path'] == path), None)
        changeset = os.path.join(version.project.storage.project_dir, file['diff']['location'])
        json_file = 'changeset'

        # create manually list changes
        version.project.storage.geodiff.list_changes(
            changeset, json_file
        )
        list_changes = json.loads(open(json_file, 'r').read())
        os.remove(json_file)

        # compare manually created with data from request
        assert json.loads(resp.data) == list_changes['geodiff']


def test_get_projects_by_uuids(client):
    user = User.query.filter_by(username="mergin").first()
    p1 = create_project('foo', test_namespace, user)
    user2 = add_user('user2', 'ilovemergin')
    p2 = create_project('foo', 'user2', user2)
    uuids = ",".join([str(p1.id), str(p2.id), "1234"])

    resp = client.get(f'/v1/project/by_uuids?uuids={uuids}')
    assert resp.status_code == 200
    resp_data = [str(project["id"]) for project in json.loads(resp.data)]
    assert str(p1.id) in resp_data  # user has access to
    assert str(p2.id) not in resp_data  # belongs to user2, and user does not have access
    assert "1234" not in resp_data  # invalid id

    uuids = ",".join([str(uuid.uuid4()) for _ in range(0, 11)])
    resp = client.get(f'/v1/project/by_uuids?uuids={uuids}')
    assert resp.status_code == 400

    resp = client.get(f'/v1/project/by_uuids')
    assert resp.status_code == 400
