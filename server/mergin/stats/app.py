# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from flask import Flask

from .config import Configuration


def register(app: Flask):
    """Register mergin statistics module in Flask app"""
    app.config.from_object(Configuration)
    app.connexion_app.add_api(
        "stats/api.yaml",
        base_path="/",
        options={"swagger_ui": False, "serve_spec": False},
        validate_responses=True,
    )
    app.blueprints["/"].name = "stats"
    app.blueprints["stats"] = app.blueprints.pop("/")
