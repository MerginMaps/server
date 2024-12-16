# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import requests
import datetime
import json
import logging
from flask import current_app
from sqlalchemy.sql.operators import is_

from .models import MerginInfo
from ..celery import celery
from ..app import db
from ..auth.models import User
from ..sync.models import Project


@celery.task(ignore_result=True)
def send_statistics():
    """Send statistics about usage."""
    """
      "service_id": <acquired service_id> *required
      "url": <server url> *optional
      "licence": <ce/ee> *optional
      "projects_count": <number of projects on the server> *optional
      "users_count": <number of users on the server> *optional
      "workspaces_count": <number of workspaces on the server> *optional
      "last_change": <datetime of the latest change in UTC> *optional
      "server_version": <CE/EE service server version> *optional
    """

    if not current_app.config["COLLECT_STATISTICS"]:
        return

    if not db.engine.has_table("mergin_info"):
        logging.warning("Database not initialized")
        return

    info = MerginInfo.query.first()
    if not info:
        # create new info with random service id
        service_id = current_app.config.get("SERVICE_ID", None)
        info = MerginInfo(service_id)
        db.session.add(info)
        db.session.commit()

    if (
        info.last_reported
        and datetime.datetime.utcnow()
        < info.last_reported + datetime.timedelta(hours=12)
    ):
        return

    last_change_item = (
        db.session.query(Project.updated).order_by(Project.updated.desc()).first()
    )

    data = {
        "service_uuid": str(info.service_id),
        "url": current_app.config["MERGIN_BASE_URL"],
        "contact_email": current_app.config["CONTACT_EMAIL"],
        "licence": current_app.config["SERVER_TYPE"],
        "projects_count": Project.query.filter(Project.removed_at.is_(None)).count(),
        "users_count": User.query.filter(
            is_(User.username.ilike("deleted_%"), False)
        ).count(),
        "workspaces_count": current_app.ws_handler.workspace_count(),
        "last_change": str(last_change_item.updated) + "Z" if last_change_item else "",
        "server_version": current_app.config["VERSION"],
        "monthly_contributors": current_app.ws_handler.monthly_contributors_count(),
        "editors": current_app.ws_handler.server_editors_count(),
    }

    try:
        resp = requests.post(
            current_app.config["STATISTICS_URL"] + "/usage-statistic",
            data=json.dumps(data),
        )
        if resp.ok:
            info.last_reported = datetime.datetime.utcnow()
            db.session.commit()
        else:
            logging.warning("Statistics error: " + str(resp.text))
    except requests.exceptions.RequestException as e:
        logging.warning("Statistics error: " + str(e))
