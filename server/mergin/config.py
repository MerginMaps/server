# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
from .version import get_version
from decouple import config, Csv

config_dir = os.path.abspath(os.path.dirname(__file__))


class Configuration(object):
    DEBUG = config("FLASK_DEBUG", default=False, cast=bool)
    TESTING = config("TESTING", default=False, cast=bool)
    SECRET_KEY = config("SECRET_KEY")
    PROXY_FIX = config("PROXY_FIX", default=True, cast=bool)
    SWAGGER_UI = config(
        "SWAGGER_UI", default=False, cast=bool
    )  # to enable swagger UI console (for tests only)
    VERSION = config("VERSION", default=get_version())
    PUBLIC_DIR = config(
        "PUBLIC_DIR", default=os.path.join(config_dir, os.pardir, "build", "static")
    )

    # Mergin DB related
    SQLALCHEMY_TRACK_MODIFICATIONS = config(
        "SQLALCHEMY_TRACK_MODIFICATIONS", default=False, cast=bool
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": config("DB_POOL_SIZE", default=2, cast=int),
        # max_overflow set to SQLAlchemy default https://docs.sqlalchemy.org/en/14/core/engines.html
        "max_overflow": config("DB_POOL_MAX_OVERFLOW", default=10, cast=int),
        "pool_timeout": config("DB_POOL_TIMEOUT", default=300, cast=int),
    }
    DB_USER = config("DB_USER", default="postgres")
    DB_PASSWORD = config("DB_PASSWORD", default="postgres")
    DB_HOST = config("DB_HOST", default="localhost")
    DB_PORT = config("DB_PORT", default=5002, cast=int)
    DB_DATABASE = config("DB_DATABASE", default="postgres")
    DB_APPLICATION_NAME = config("DB_APPLICATION_NAME", default="mergin")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?application_name={DB_APPLICATION_NAME}",
    )

    WTF_CSRF_TIME_LIMIT = config(
        "WTF_CSRF_TIME_LIMIT", default=3600 * 24, cast=int
    )  # in seconds
    WTF_CSRF_ENABLED = config("WTF_CSRF_ENABLED", default=True, cast=bool)

    # for flask mail
    MAIL_SERVER = config("MAIL_SERVER", default="localhost")
    MAIL_PORT = config("MAIL_PORT", default=587, cast=int)
    MAIL_USE_TLS = config("MAIL_USE_TLS", default=True, cast=bool)
    MAIL_DEFAULT_SENDER = config("MAIL_DEFAULT_SENDER")
    MAIL_BCC = config("MAIL_BCC")
    MAIL_USERNAME = config("MAIL_USERNAME")
    MAIL_PASSWORD = config("MAIL_PASSWORD")
    MAIL_DEBUG = config("MAIL_SUPPRESS_SEND", default=False, cast=bool)
    MAIL_SUPPRESS_SEND = config("MAIL_SUPPRESS_SEND", default=True, cast=bool)

    # celery
    CELERY_IMPORTS = config(
        "CELERY_IMPORTS", default="mergin.celery", cast=Csv(post_process=tuple)
    )
    BROKER_URL = config("BROKER_URL", default="redis://172.17.0.1:6379/0")
    BROKER_TRANSPORT_OPTIONS = config(
        "BROKER_TRANSPORT_OPTIONS", default="{}", cast=eval
    )
    CELERY_RESULT_BACKEND = config(
        "CELERY_RESULT_BACKEND", default="redis://172.17.0.1:6379/0"
    )
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = config(
        "CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS", default="{}", cast=eval
    )

    # deployment URL (e.g. for links generated in emails)
    MERGIN_BASE_URL = config("MERGIN_BASE_URL", default="")
    # for link to logo in emails
    MERGIN_LOGO_URL = config("MERGIN_LOGO_URL", default="")

    MERGIN_SUBSCRIPTIONS = config("MERGIN_SUBSCRIPTIONS", default=False, cast=bool)
    MERGIN_TESTING = config("MERGIN_TESTING", default=False, cast=bool)
    DOCS_URL = config("DOCS_URL", default="https://merginmaps.com/docs").rstrip("/")

    # default workspace settings
    GLOBAL_WORKSPACE = config("GLOBAL_WORKSPACE", default="mergin")
    GLOBAL_STORAGE = config("GLOBAL_STORAGE", default=1024 * 1024 * 1024, cast=int)
    GLOBAL_READ = config("GLOBAL_READ", default=False, cast=bool)
    GLOBAL_WRITE = config("GLOBAL_WRITE", default=False, cast=bool)
    GLOBAL_ADMIN = config("GLOBAL_ADMIN", default=False, cast=bool)

    SERVER_TYPE = config("SERVER_TYPE", default="")
    # can users create their own account or is it reserved for superuser only
    USER_SELF_REGISTRATION = config("USER_SELF_REGISTRATION", default=False, cast=bool)
    # build hash number
    BUILD_HASH = config("BUILD_HASH", default="")
