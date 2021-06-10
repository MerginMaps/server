import json
from flask import url_for
from flask_login import AnonymousUserMixin
from sqlalchemy.orm.attributes import flag_modified

from src.permissions import require_project, ProjectPermissions
from src.models.db_models import Namespace, Project, ProjectAccess
from src.auth.models import User
from src import db
from .utils import login, add_user, create_project
from . import json_headers, TEST_ORG, DEFAULT_USER


def test_organisation_permissions(client, test_organisation):
    user = add_user("random", "random")
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    project = create_project("foo", TEST_ORG, admin)

    assert not ProjectPermissions.Upload.check(project,  user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project,  user)

    test_organisation.readers.append(user.id)
    flag_modified(test_organisation, "readers")
    db.session.commit()

    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)

    test_organisation.writers.append(user.id)
    flag_modified(test_organisation, "writers")
    db.session.commit()

    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)


def test_project_permissions(client):
    data = {"name": 'foo'}
    resp = client.post('/v1/project/{}'.format("mergin"), data=json.dumps(data), headers=json_headers)

    user = add_user("random", "random")
    project = Project.query.filter_by(name="foo", namespace="mergin").first()

    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)

    pa = project.access
    pa.readers.append(user.id)
    flag_modified(pa, "readers")
    db.session.commit()

    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)

    pa.writers.append(user.id)
    flag_modified(pa, "writers")
    db.session.commit()

    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert not ProjectPermissions.Delete.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)

    # when users is removed from readers can not read a project anymore but still can write into it
    pa.readers.clear()
    flag_modified(pa, "readers")
    db.session.commit()

    assert not ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)

    # testing owner permissions
    user = User.query.filter_by(username='mergin').first()

    assert ProjectPermissions.Read.check(project, user)
    assert ProjectPermissions.Upload.check(project, user)
    assert ProjectPermissions.Delete.check(project, user)
    assert ProjectPermissions.Update.check(project, user)

    # test AnonymousUserMixin
    client.get(url_for('auth.logout'))
    user = AnonymousUserMixin()
    assert not ProjectPermissions.Read.check(project, user)
    project.access.public = True
    db.session.commit()
    assert ProjectPermissions.Read.check(project, user)
    assert not ProjectPermissions.Update.check(project, user)
    assert not ProjectPermissions.Upload.check(project, user)


def test_permission_to_create_project(client, test_organisation):
    user = add_user("random", "random")
    login(client, "random", "random")
    resp = client.post('/v1/project/{}'.format(TEST_ORG), data=json.dumps({"name": "foo"}), headers=json_headers)
    assert resp.status_code == 403

    test_organisation.readers.append(user.id)
    flag_modified(test_organisation, "readers")
    db.session.commit()
    resp = client.post('/v1/project/{}'.format(TEST_ORG), data=json.dumps({"name": "foo"}), headers=json_headers)
    assert resp.status_code == 403

    test_organisation.writers.append(user.id)
    flag_modified(test_organisation, "writers")
    db.session.commit()
    resp = client.post('/v1/project/{}'.format(TEST_ORG), data=json.dumps({"name": "foo"}), headers=json_headers)
    assert resp.status_code == 200

    resp = client.post('/v1/project/{}'.format("mergin"), data=json.dumps({"name": "foo"}), headers=json_headers)
    assert resp.status_code == 403
