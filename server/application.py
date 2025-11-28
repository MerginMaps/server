# Copyright (C) Lutra Consulting Limited
# SPDX-FileCopyrightText: 2018 Lutra Consulting Limited <info@merginmaps.com>
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
# we need to monkey patch before app is loaded resolve this:
# "gunicorn/workers/ggevent.py:65: MonkeyPatchWarning: Monkey-patching ssl after ssl has already been imported may lead
# to errors, including RecursionError on Python 3.6. It may also silently lead to incorrect behaviour on Python 3.7.
# Please monkey-patch earlier. See https://github.com/gevent/gevent/issues/1016.
# Modules that had direct imports (NOT patched): ['urllib3.util, 'urllib3.util.ssl']"
# which comes from using requests (its deps) lib in webhooks

from mergin.config import Configuration as MainConfig

if MainConfig.GEVENT_WORKER:
    import gevent.monkey
    import psycogreen.gevent

    gevent.monkey.patch_all()
    psycogreen.gevent.patch_psycopg()

from a2wsgi import ASGIMiddleware
from random import randint
from celery.schedules import crontab
from mergin.app import create_app
from mergin.auth.tasks import anonymize_removed_users
from mergin.sync.tasks import (
    remove_projects_archives,
    remove_temp_files,
    remove_projects_backups,
    remove_unused_chunks,
)
from mergin.celery import celery, configure_celery
from mergin.stats.config import Configuration
from mergin.stats.tasks import save_statistics, send_statistics
from mergin.stats.app import register as register_stats

Configuration.SERVER_TYPE = "ce"
Configuration.USER_SELF_REGISTRATION = False

application = create_app(
    [
        "DOCS_URL",
        "SERVER_TYPE",
        "COLLECT_STATISTICS",
        "USER_SELF_REGISTRATION",
        "GLOBAL_ADMIN",
        "GLOBAL_READ",
        "GLOBAL_WRITE",
        "ENABLE_SUPERADMIN_ASSIGNMENT",
        "DIAGNOSTIC_LOGS_URL",
        "V2_PUSH_ENABLED",
    ]
)
register_stats(application)
# patch celery object with application settings and attach flask context to it
configure_celery(celery, application, ["mergin.auth", "mergin.sync", "mergin.stats"])


# set up period celery tasks
@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        anonymize_removed_users,
        name="anonymize inactive users",
    )
    sender.add_periodic_task(
        crontab(hour=2, minute=0), remove_temp_files, name="clean temp files"
    )
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        remove_projects_backups,
        name="remove old project backups",
    )
    sender.add_periodic_task(
        crontab(hour="*/12", minute=0),
        save_statistics,
        name="Save usage statistics to database",
    )
    if Configuration.COLLECT_STATISTICS:
        sender.add_periodic_task(
            crontab(hour=randint(0, 5), minute=randint(0, 60)),
            send_statistics,
            name="send usage statistics",
        )
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        remove_projects_archives,
        name="remove old project archives",
    ),
    sender.add_periodic_task(
        crontab(hour="*/4", minute=0),
        remove_unused_chunks,
        name="clean up of outdated chunks",
    )


wsgi_app = ASGIMiddleware(application.connexion_app)

if __name__ == "__main__":
    # run starlette development server
    application.connexion_app.run(
        host="0.0.0.0",
        port=5000,
    )
