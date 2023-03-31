#!/bin/bash

# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

# make sure all files created by gunicorn (mergin server) have proper permissions
umask 0027

# Settings passed to gunicorn have the following order of precedence
# (tested using --workers):
#
# 1. Command-line (highest)
# 2. Environment variable
# 3. File referenced by --config (lowest)
#
# We store a base config in config.py and override things as needed
# using the environment variable GUNICORN_CMD_ARGS.

/bin/bash -c "celery -A application.celery beat --loglevel=info &"
/bin/bash -c "celery -A application.celery worker --loglevel=info &"
/bin/bash -c "gunicorn --config config.py application:application"
