# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from wtforms import Field, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class IntegerListField(Field):
    def _value(self):
        return self.data

    def process_formdata(self, valuelist):
        self.data = valuelist


class AccessPermissionForm(FlaskForm):
    permissions = SelectField(
        "permissions",
        [DataRequired()],
        choices=[
            ("read", "read"),
            ("edit", "edit"),
            ("write", "write"),
            ("owner", "owner"),
        ],
    )
