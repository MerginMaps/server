# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from ..auth.forms import LoginForm


class ApiLoginForm(LoginForm):
    class Meta:
        csrf = False

