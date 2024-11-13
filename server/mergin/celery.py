# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from typing import List
from celery import Celery
from flask import Flask
from flask_mail import Message
from smtplib import SMTPException, SMTPServerDisconnected

from .config import Configuration
from .app import mail


# create on flask app independent object
# we need this for defining tasks, and celery is then configured in run_celery.py
celery = Celery(
    __name__,
    broker=Configuration.BROKER_URL,
    backend=Configuration.CELERY_RESULT_BACKEND,
)


@celery.task(
    autoretry_for=(
        SMTPException,
        SMTPServerDisconnected,
    ),
    retry_kwargs={"max_retries": 3, "default_retry_delay": 300},
    ignore_result=True,
)
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
        msg.bcc.append(Configuration.MAIL_BCC)
    mail.send(msg)


def configure_celery(celery: Celery, app: Flask, packages: List[str]):
    """Initialize celery object to work with flask app.
    Attach flask context and register tasks from packages
    """

    class ContextTask(celery.Task):
        """Attach flask app context to celery task"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.conf.update(app.config)
    celery.conf.update(
        task_acks_late=Configuration.CELERY_ACKS_LATE,
        worker_concurrency=Configuration.CELERYD_CONCURRENCY,
        worker_prefetch_multiplier=Configuration.CELERYD_PREFETCH_MULTIPLIER,
    )
    # configure celery with flask context https://flask.palletsprojects.com/en/1.1.x/patterns/celery/
    # e.g. for using flask-mail
    celery.Task = ContextTask
    # load tasks from packages (e.g. auth.tasks from auth package)
    celery.autodiscover_tasks(packages)
