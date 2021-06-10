# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from ..auth.forms import LoginForm


class ApiLoginForm(LoginForm):
    class Meta:
        csrf = False

