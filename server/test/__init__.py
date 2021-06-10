# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import os
import tempfile

# constants
test_namespace = 'mergin'
test_project = 'test'
test_project_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_projects', test_project)
json_headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
DEFAULT_USER = ('mergin', 'ilovemergin')  # username, password - is a super user
TMP_DIR = tempfile.gettempdir()
TEST_ORG = "mergin.org"
