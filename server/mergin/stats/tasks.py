# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from dataclasses import asdict
import requests
from datetime import datetime, timedelta
import json
import logging
from flask import current_app
from sqlalchemy.sql.operators import is_
from sqlalchemy import inspect
from sqlalchemy.sql import select, func

from .models import MerginInfo, MerginStatistics, ServerCallhomeData
from ..celery import celery
from ..app import db
from ..auth.models import User
from ..sync.models import Project


def get_callhome_data(info: MerginInfo | None = None) -> ServerCallhomeData:
    """
    Get data about server to send to callhome service
    """
    last_change = db.session.scalars(
        select(Project.updated).order_by(Project.updated.desc())
    ).first()
    service_uuid = str(info.service_id) if info else None
    data = ServerCallhomeData(
        service_uuid=service_uuid,
        url=current_app.config["MERGIN_BASE_URL"],
        contact_email=current_app.config["CONTACT_EMAIL"],
        licence=current_app.config["SERVER_TYPE"],
        projects_count=db.session.scalar(
            select(func.count(Project.id)).where(is_(Project.removed_at, None))
        ),
        users_count=db.session.scalar(
            select(func.count(User.id)).where(
                is_(User.username.ilike("deleted_%"), False)
            )
        ),
        workspaces_count=current_app.ws_handler.workspace_count(),
        last_change=str(last_change) + "Z" if last_change else "",
        server_version=current_app.config["VERSION"],
        monthly_contributors=current_app.ws_handler.monthly_contributors_count(),
        editors=current_app.ws_handler.server_editors_count(),
        sso_connections=current_app.ws_handler.sso_connections_count(),
    )
    return data


@celery.task(ignore_result=True)
def save_statistics():
    """Save statistics about usage."""
    info = db.session.execute(select(MerginInfo)).scalar_one_or_none()
    data = get_callhome_data(info)
    stat = MerginStatistics(data=data)
    db.session.add(stat)
    db.session.commit()


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

    inspect_engine = inspect(db.engine)
    if not inspect_engine.has_table("mergin_info"):
        logging.warning("Database not initialized")
        return

    info = db.session.execute(select(MerginInfo)).scalar_one_or_none()
    if not info:
        # create new info with random service id
        service_id = current_app.config.get("SERVICE_ID", None)
        info = MerginInfo(service_id)
        db.session.add(info)
        db.session.commit()

    if info.last_reported and datetime.utcnow() < info.last_reported + timedelta(
        hours=12
    ):
        return

    data = asdict(get_callhome_data(info))

    try:
        resp = requests.post(
            current_app.config["STATISTICS_URL"] + "/usage-statistic",
            data=json.dumps(data),
        )
        if resp.ok:
            info.last_reported = datetime.utcnow()
            db.session.commit()
        else:
            logging.warning("Statistics error: " + str(resp.text))
    except requests.exceptions.RequestException as e:
        logging.warning("Statistics error: " + str(e))
