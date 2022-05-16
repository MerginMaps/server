# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import shutil
import os
from datetime import datetime, timedelta
from celery import Celery
from flask_mail import Message
from smtplib import SMTPException, SMTPServerDisconnected
from celery.schedules import crontab
from sqlalchemy import  and_, false

from .organisation import Organisation
from .auth import User
from .models.db_models import RemovedProject, Account, Project
from .config import Configuration
from . import mail, db
from .storages.disk import move_to_tmp


# create on flask app independent object
# we need this for defining tasks, and celery is then configured in run_celery.py
celery = Celery(__name__, broker=Configuration.CELERY_BROKER_URL, backend=Configuration.CELERY_RESULT_BACKEND)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=2, minute=0), remove_temp_files, name='clean temp files')
    sender.add_periodic_task(crontab(hour=2, minute=0), remove_projects_backups, name='remove old project backups')
    sender.add_periodic_task(crontab(hour=1, minute=0), remove_accounts_data, name='remove personal data of inactive users')


@celery.task(
    autoretry_for=(SMTPException, SMTPServerDisconnected, ),
    retry_kwargs={'max_retries': 3, 'default_retry_delay': 300},
    ignore_result=True)
def send_email_async(**kwargs):
    """
    Send flask mail (application context needed).

    :param email_data: content for flask mail Message
    :param email_data: dict
    """
    return send_email(**kwargs)


def send_email(**kwargs):
    """
    Send flask mail (application context needed).

    :param email_data: content for flask mail Message
    :param email_data: dict
    """
    msg = Message(**kwargs)
    # let's add default sender to BCC on production/staging server to make sure emails are in inbox
    if not Configuration.MERGIN_TESTING:
        msg.bcc.append(Configuration.MAIL_DEFAULT_SENDER)
    mail.send(msg)


@celery.task
def remove_temp_files():
    """ Remove old temp folders in mergin temp directory.
    This is clean up for storages.disk.move_to_tmp() function.
    """
    for dir in os.listdir(Configuration.TEMP_DIR):
        # ignore folder with apple notifications receipts which we want (temporarily) to maintain
        if dir == 'notifications':
            continue
        path = os.path.join(Configuration.TEMP_DIR, dir)
        if datetime.fromtimestamp(os.path.getmtime(path)) < datetime.utcnow() - timedelta(days=Configuration.TEMP_EXPIRATION):
            try:
                shutil.rmtree(path)
            except OSError as e:
                print(f"Unable to remove {path}: {str(e)}")


@celery.task
def remove_projects_backups():
    """ Permanently remove deleted projects. All data is lost, and project could not be restored anymore """
    projects = RemovedProject.query.filter(
        RemovedProject.timestamp < datetime.utcnow() - timedelta(days=Configuration.DELETED_PROJECT_EXPIRATION)
    ).all()

    for p in projects:
        p_dir = os.path.abspath(os.path.join(Configuration.LOCAL_PROJECTS, p.properties["storage_params"]["location"]))
        if os.path.exists(p_dir):
            move_to_tmp(p_dir)
        db.session.delete(p)
    db.session.commit()


@celery.task
def remove_accounts_data():
    before_expiration = datetime.today() - timedelta(days=Configuration.CLOSED_ACCOUNT_EXPIRATION)

    # regex condition to account name to avoid process deleted accounts multiple times
    subquery = db.session.query(User.id).filter(User.active == false(), User.inactive_since <= before_expiration, User.username.op("~")('^(?!deleted_\d{13})')).subquery()
    subquery2 = db.session.query(Organisation.id).filter(Organisation.active == false(), Organisation.inactive_since <= before_expiration, Organisation.name.op("~")('^(?!deleted_\d{13})')).subquery()
    accounts = Account.query.filter(and_(Account.owner_id.in_(subquery), Account.type == "user") | and_(Account.owner_id.in_(subquery2), Account.type == "organisation"))

    for account in accounts:
        timestamp = round(datetime.now().timestamp() * 1000)
        user = None
        organisation = None
        if account.type == 'user':
            user = User.query.get(account.owner_id)

            user.username = f"deleted_{timestamp}"
            user.email = f"deleted_{timestamp}"
            user.verified_email = False
            user.assign_password(f"deleted_{timestamp}")
            user.profile.firs_name = ""
            user.profile.last_name = ""

        else:
            organisation = Organisation.query.get(account.owner_id)
            organisation.name = f"deleted_{timestamp}"
            organisation.description = ""

        # delete account's projects
        projects = Project.query.filter_by(namespace=account.namespace.name).all()
        for p in projects:
            p_dir = p.storage.project_dir
            if os.path.exists(p_dir):
                move_to_tmp(p_dir)
            db.session.delete(p)

        # delete account's removed projects
        projects = RemovedProject.query.filter_by(namespace=account.namespace.name).all()
        for p in projects:
            p_dir = os.path.abspath(os.path.join(Configuration.LOCAL_PROJECTS, p.properties["storage_params"]["location"]))
            if os.path.exists(p_dir):
                move_to_tmp(p_dir)
            db.session.delete(p)

        db.session.commit()
        account.namespace.name = f"deleted_{timestamp}"

    db.session.commit()
