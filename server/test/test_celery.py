import os
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Mail
from unittest.mock import patch
from sqlalchemy.orm.attributes import flag_modified

from src import db
from src.config import Configuration
from src.organisation import Organisation
from src.auth.models import User, LoginHistory
from src.models.db_models import Project, RemovedProject, Namespace
from src.celery import send_email_async, remove_temp_files, remove_projects_backups, remove_accounts_data
from src.celery import remove_temp_files, remove_projects_backups
from src.storages.disk import move_to_tmp
from . import test_project, test_namespace
from .utils import create_project, cleanup, add_user, create_organisation


def test_send_email(app):
    """ Test celery is actually sending emails. """
    mail = Mail()
    email_data = {
        'subject': 'test',
        'html': 'test',
        'recipients': ['foo@bar.com'],
        'sender': 'no_reply@cloudmergin.com'
    }
    with mail.record_messages() as outbox:
        Configuration.MERGIN_TESTING = True
        task = send_email_async.s(**email_data).apply()
        assert len(outbox) == 1
        assert task.status == 'SUCCESS'
        assert outbox[0].sender == 'no_reply@cloudmergin.com'
        assert outbox[0].html == 'test'
        assert outbox[0].subject == 'test'
        assert current_app.config['MAIL_DEFAULT_SENDER'] not in outbox[0].bcc
        assert 'foo@bar.com' in outbox[0].send_to

        # turn off testing mode
        Configuration.MERGIN_TESTING = False
        task = send_email_async.s(**email_data).apply()
        assert len(outbox) == 2
        assert task.status == 'SUCCESS'
        assert current_app.config['MAIL_DEFAULT_SENDER'] in outbox[1].bcc

    Configuration.MERGIN_TESTING = True
    del email_data['recipients']
    task = send_email_async.s(**email_data).apply()
    assert task.status == 'FAILURE'
    assert 'No recipients have been added' in task.traceback


@patch('src.celery.send_email_async.apply_async')
def test_send_email_from_flask(send_email_mock, client):
    """ Test correct data are passed to celery task which is called from endpoint. """
    project = Project.query.filter_by(namespace='mergin', name='test').first()
    email_data = {
        'subject': 'Mergin project mergin/test has been deleted',
        'recipients': [project.creator.email],
        'sender': current_app.config['MAIL_DEFAULT_SENDER']
    }
    resp = client.delete('/v1/project/{}/{}'.format('mergin', 'test'))
    assert resp.status_code == 200
    # cleanup files
    cleanup(client, [project.storage.project_dir])
    assert send_email_mock.called
    call_args, _ = send_email_mock.call_args
    _, kwargs = call_args
    del kwargs['html']
    assert email_data == kwargs


def test_clean_temp_files(app):
    project = Project.query.filter_by(name=test_project, namespace=test_namespace).first()
    # pretend project has been removed
    path = move_to_tmp(project.storage.project_dir)
    assert os.path.exists(path)
    # try with default value, dir is still not marked for removal
    remove_temp_files()
    assert os.path.exists(path)
    # patch modification time of parent dir
    t = datetime.utcnow() - timedelta(days=(app.config['TEMP_EXPIRATION']+1))
    parent_dir = os.path.dirname(os.path.dirname(path))
    os.utime(parent_dir, (datetime.timestamp(t), datetime.timestamp(t)))
    remove_temp_files()
    assert not os.path.exists(path)


def test_remove_deleted_project_backups(client):
    resp = client.delete('/v1/project/{}/{}'.format(test_namespace, test_project))
    assert resp.status_code == 200
    rp = RemovedProject.query.filter_by(namespace=test_namespace, name=test_project).first()
    rp.timestamp = datetime.utcnow() - timedelta(days=(client.application.config['DELETED_PROJECT_EXPIRATION']+1))
    rp_dir = os.path.abspath(
        os.path.join(client.application.config["LOCAL_PROJECTS"], rp.properties["storage_params"]["location"]))
    assert os.path.exists(rp_dir)
    remove_projects_backups()
    assert not RemovedProject.query.filter_by(namespace=test_namespace, name=test_project).count()
    assert not os.path.exists(rp_dir)


def test_remove_accounts_data(client):
    usr = add_user("test1", "test")
    usr2 = add_user("test2", "test")
    usr2_id = usr2.id
    org = create_organisation("test_organisation", usr)
    org_id = org.id
    p = create_project("test1", "test1", usr)
    p3 = create_project("test_delete", "test1", usr)
    p2 = create_project("test_organisation_project", "test_organisation", usr)
    project_location = p.storage.project_dir
    project2_location = p2.storage.project_dir
    project3_location = p3.storage.project_dir

    resp = client.delete('/v1/project/{}/{}'.format("test1", "test_delete"))
    assert resp.status_code == 200
    assert 1 == RemovedProject.query.filter_by(namespace="test1", name="test_delete").count()
    assert os.path.exists(project3_location)

    usr.inactive_since = datetime.today() - timedelta(days=Configuration.CLOSED_ACCOUNT_EXPIRATION + 0.5)
    usr.active = False
    usr_id = usr.id
    org.owners.append(usr2.id)
    flag_modified(org, "owners")
    db.session.add(org)
    db.session.commit()

    remove_accounts_data()

    usr = User.query.get(usr_id)
    assert "deleted" in usr.username
    assert not os.path.exists(project_location)
    namespace = Namespace.query.filter(Namespace.name == usr.username).first()
    assert namespace
    assert 0 == RemovedProject.query.filter_by(namespace="test1", name="test_delete").count()
    assert not os.path.exists(project3_location)

    org = Organisation.query.get(org_id)
    org.inactive_since = datetime.today() - timedelta(days=Configuration.CLOSED_ACCOUNT_EXPIRATION + 0.5)
    org.active = False
    db.session.commit()

    remove_accounts_data()
    org = Organisation.query.get(org_id)
    assert "deleted" in org.name
    namespace = Namespace.query.filter(Namespace.name == org.name).first()
    assert namespace
    usr2 = User.query.get(usr2_id)
    assert usr2.username == "test2"
    assert "test1" not in org.owners
    assert not os.path.exists(project2_location)
    project = Project.query.filter(Project.name == "test_organisation_project").first()
    assert not project
