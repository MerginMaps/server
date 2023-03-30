# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import requests
from flask import abort, current_app

from .config import Configuration
from ..app import parse_version_string


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
