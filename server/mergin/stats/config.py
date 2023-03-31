# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from decouple import config


class Configuration(object):
    # send statistics about usage
    COLLECT_STATISTICS = config("COLLECT_STATISTICS", default=True, cast=bool)
    # deployment uuid
    SERVICE_ID = config("SERVICE_ID", default="")
    # monitoring service URL
    STATISTICS_URL = config(
        "STATISTICS_URL", default="https://api.merginmaps.com/monitoring/v1"
    ).rstrip("/")
