import json
import logging
import os
from flask import abort, current_app, request
from flask_login import current_user
from magic import from_buffer
import time

import requests

from .utils import save_diagnostic_log_file
from .app import parse_version_string, db


def get_latest_version():
    """Parse information about available server updates from 3rd party service"""
    try:
        req = requests.get(current_app.config["STATISTICS_URL"] + "/latest-versions")
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


def save_diagnostic_log():
    """Save diagnostic logs"""
    # if server is using external storage, we don't want to save logs
    if current_app.config.get("DIAGNOSTIC_LOGS_URL"):
        abort(404)

    # check if plain text body is not larger than 1MB
    max_size = current_app.config.get("DIAGNOSTIC_LOGS_MAX_SIZE")
    if request.content_length > max_size:
        abort(413)
    # get body from request
    body = request.get_data()
    if not body:
        abort(400)
    if len(body) > max_size:
        abort(413)
    mime_type = from_buffer(body, mime=True)
    if mime_type != "text/plain":
        abort(400)

    app = request.args.get("app")
    username = current_user.username if current_user.is_authenticated else "anonymous"
    save_diagnostic_log_file(app, username, body)

    return "Log saved successfully", 200
