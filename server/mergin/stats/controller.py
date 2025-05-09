# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import requests
from flask import abort, current_app, make_response, request
from datetime import datetime, time
from csv import DictWriter
from pathvalidate import sanitize_filename

from mergin.auth.app import auth_required
from mergin.stats.models import MerginStatistics, ServerCallhomeData
from mergin.stats.utils import save_diagnostic_log_file

from .config import Configuration
from ..app import parse_version_string, db


class CsvTextBuilder(object):
    """
    Mock csv writer that writes to text buffer
    """

    def __init__(self):
        self.data = []

    def write(self, row):
        self.data.append(row)


def get_latest_version():
    """Parse information about available server updates from 3rd party service"""
    try:
        req = requests.get(Configuration.STATISTICS_URL + "/latest-versions")
    except requests.exceptions.RequestException:
        abort(400, "Updates information not available")

    if not req.ok:
        abort(400, "Updates information not available")

    data = req.json().get(current_app.config["SERVER_TYPE"].lower(), None)
    if not data:
        abort(400, "Updates information not available")

    parsed_version = parse_version_string(data.get("version", ""))
    if not parsed_version:
        abort(400, "Updates information not available")

    data = {**data, **parsed_version}
    return data, 200


@auth_required(permissions=["admin"])
def download_report(date_from: str, date_to: str):
    """Download statistics from server instance"""
    try:
        # try to validate dates to prevent unhandled date formats
        # add start of the day time and end of the day time to prevent bad filtering in db
        parsed_from = datetime.combine(
            datetime.strptime(date_from, "%Y-%m-%d"), time.min
        )
        parsed_to = datetime.combine(datetime.strptime(date_to, "%Y-%m-%d"), time.max)
    except ValueError:
        abort(400, "Invalid date format")

    stats = (
        db.session.query(MerginStatistics.created_at, MerginStatistics.data)
        .filter(MerginStatistics.created_at.between(parsed_from, parsed_to))
        .order_by(MerginStatistics.created_at.desc())
        .all()
    )
    created_column = "created_at"
    data = [
        {
            **stat.data,
            "created_at": datetime.isoformat(stat.created_at),
        }
        for stat in stats
    ]
    columns = list(ServerCallhomeData.__dataclass_fields__.keys()) + [created_column]
    # get columns for data, this is usefull when we will update data json format (removing columns, adding new ones)

    builder = CsvTextBuilder()
    writer = DictWriter(builder, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    csv_data = "".join(builder.data)
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=usage-report.csv"
    response.mimetype = "text/csv"
    return response


def save_diagnostic_log(app: str, username: str):
    """Save diagnostic logs"""
    # if server is using external storage, we don't want to save logs
    if current_app.config.get("DIAGNOSTIC_LOGS_URL"):
        abort(404)

    # check if plain text body is not larger than 1MB
    max_size = 1024 * 1024
    if request.content_length > max_size:
        abort(413)
    # get body from request
    body = request.get_data()
    if not body:
        abort(400)
    if len(body) > max_size:
        abort(413)

    # save diagnostic log file
    folder = current_app.config.get("DIAGNOSTIC_LOGS_DIR")
    save_diagnostic_log_file(
        app, username, body, current_app.config.get("DIAGNOSTIC_LOGS_DIR")
    )

    return "Log saved successfully", 200
