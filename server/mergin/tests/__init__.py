# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
import tempfile

# constants
test_workspace_name = "mergin"
test_workspace_id = 1
test_project = "test"
test_project_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "test_projects", test_project
)
json_headers = {"Content-Type": "application/json", "Accept": "application/json"}
DEFAULT_USER = ("mergin", "ilovemergin")  # username, password - is a super user
TMP_DIR = tempfile.gettempdir()
