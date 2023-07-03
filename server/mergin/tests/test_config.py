# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial


def test_config(client):
    """Test response of app public config"""
    resp = client.get("/config")
    assert resp.status_code == 200
    # check we expose only what was intended
    assert set(resp.json.keys()) == {
        "docs_url",
        "server_type",
        "blacklist_dirs",
        "blacklist_files",
        "version",
        "collect_statistics",
        "server_configured",
        "fix",
        "major",
        "minor",
    }
    resp = client.get("/config")
    assert resp.status_code == 200
    assert resp.json["server_type"] == "ce"

    client.application.config["VERSION"] = "2023.1.2"
    resp = client.get("/config")
    assert resp.json["major"] == 2023
    assert resp.json["minor"] == 1
    assert resp.json["fix"] == 2

    assert resp.json["server_configured"] is False
    client.application.config["MERGIN_BASE_URL"] = "http://localhost:5000"
    resp = client.get("/config")
    assert resp.json["server_configured"] is True
