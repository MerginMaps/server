# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from . import create_app
from .celery import celery

app = create_app()
celery.conf.update(app.config)


# configure celery with flask context https://flask.palletsprojects.com/en/1.1.x/patterns/celery/
# e.g. for using flask-mail
class ContextTask(celery.Task):
    """ Attach flask app context to celery task """
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask
