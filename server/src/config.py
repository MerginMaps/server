# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import os
from tempfile import tempdir
from .version import get_version
from decouple import config, Csv

config_dir = os.path.abspath(os.path.dirname(__file__))


class Configuration(object):
    DEBUG = config('FLASK_DEBUG', default=False, cast=bool)
    TESTING = config('TESTING', default=False, cast=bool)
    SECRET_KEY = config('SECRET_KEY')
    PROXY_FIX = config('PROXY_FIX', default=True, cast=bool)
    SWAGGER_UI = config('SWAGGER_UI', default=False, cast=bool)  # to enable swagger UI console (for test only)
    VERSION = config('VERSION', default=get_version())
    PUBLIC_DIR = config('PUBLIC_DIR', default=os.path.join(config_dir, os.pardir, 'build', 'static'))
    # for local storage type
    LOCAL_PROJECTS = config('LOCAL_PROJECTS', default=os.path.join(config_dir, os.pardir, os.pardir, 'projects'))

    # Mergin DB related
    SQLALCHEMY_TRACK_MODIFICATIONS = config('SQLALCHEMY_TRACK_MODIFICATIONS', default=False, cast=bool)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 2,
        'pool_timeout': 300
    }
    DB_USER = config('DB_USER', default='postgres')
    DB_PASSWORD = config('DB_PASSWORD', default='postgres')
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default=5002, cast=int)
    DB_DATABASE = config('DB_DATABASE', default='postgres')
    DB_APPLICATION_NAME = config('DB_APPLICATION_NAME', default='mergin')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?application_name={DB_APPLICATION_NAME}')

    # auth related
    SECURITY_PASSWORD_SALT = config('SECURITY_PASSWORD_SALT')
    WTF_CSRF_TIME_LIMIT = config('WTF_CSRF_TIME_LIMIT', default=3600 * 24, cast=int)  # in seconds
    BEARER_TOKEN_EXPIRATION = config('BEARER_TOKEN_EXPIRATION', default=3600 * 12, cast=int)  # in seconds
    WTF_CSRF_ENABLED = config('WTF_CSRF_ENABLED', default=True, cast=bool)

    # for flask mail
    MAIL_SERVER = config('MAIL_SERVER', default='localhost')
    MAIL_PORT = config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = config('MAIL_USE_TLS', default=True, cast=bool)
    MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER')
    MAIL_USERNAME = config('MAIL_USERNAME')
    MAIL_PASSWORD = config('MAIL_PASSWORD')
    MAIL_DEBUG = config('MAIL_SUPPRESS_SEND', default=False, cast=bool)
    MAIL_SUPPRESS_SEND = config('MAIL_SUPPRESS_SEND', default=True, cast=bool)

    USER_SELF_REGISTRATION = config('USER_SELF_REGISTRATION', default=True, cast=bool)

    # locking file when backups are created
    MAINTENANCE_FILE = config('MAINTENANCE_FILE', default=os.path.join(LOCAL_PROJECTS, 'MAINTENANCE'))

    # data sync
    LOCKFILE_EXPIRATION = config('LOCKFILE_EXPIRATION', default=300, cast=int)  # in seconds
    MAX_CHUNK_SIZE = config('MAX_CHUNK_SIZE', default=10 * 1024 * 1024, cast=int)  # in bytes
    USE_X_ACCEL = config('USE_X_ACCEL', default=False, cast=bool)  # use nginx (in front of gunicorn) to serve files (https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/)
    FILE_EXPIRATION = config('FILE_EXPIRATION', default=48 * 3600, cast=int)  # for clean up of old files where diffs were applied, in seconds
    BLACKLIST = config('BLACKLIST', default='.mergin/, .DS_Store, .directory', cast=Csv())

    # celery
    CELERY_IMPORTS = config('CELERY_IMPORTS', default="src.celery")
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://172.17.0.1:6379/0')
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://172.17.0.1:6379/0')

    # various life times
    TRANSFER_EXPIRATION = config('TRANSFER_EXPIRATION', default=7 * 24 * 3600, cast=int)  # in seconds
    ORGANISATION_INVITATION_EXPIRATION = config('ORGANISATION_INVITATION_EXPIRATION', default=7 * 24 * 3600, cast=int)  # in seconds
    PROJECT_ACCESS_REQUEST = config('PROJECT_ACCESS_REQUEST', default=7 * 24 * 3600, cast=int)

    TEMP_EXPIRATION = config('TEMP_EXPIRATION', default=7, cast=int)  # time in days after files are permanently deleted
    CLOSED_ACCOUNT_EXPIRATION = config('CLOSED_ACCOUNT_EXPIRATION', default=5, cast=int) # time in days after user closed his account to all projects and files are permanently deleted
    DELETED_PROJECT_EXPIRATION = config('DELETED_PROJECT_EXPIRATION', default=7, cast=int)  # lifetime of deleted project, expired project are removed permanently without restore possibility, in days

    # trash dir for temp files being cleaned regularly
    TEMP_DIR = config('TEMP_DIR', default=tempdir)

    # for links generated in emails
    MERGIN_BASE_URL = config('MERGIN_BASE_URL', default="http://localhost:5000")
    # for link to logo in emails
    MERGIN_LOGO_URL = config('MERGIN_LOGO_URL', default="")

    MERGIN_SUBSCRIPTIONS = config('MERGIN_SUBSCRIPTIONS', default=False, cast=bool)
    MERGIN_TESTING = config('MERGIN_TESTING', default=False, cast=bool)
