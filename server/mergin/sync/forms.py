# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from wtforms import Field, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from mergin.sync.utils import (
    is_valid_character,
    is_valid_filename,
    is_valid_first_character,
)


def project_name_validation(name: str) -> str | None:
    """Check whether project name is valid"""
    errors = [
        "Please use only alphanumeric or these -_. characters.",
        "Project name cannot start with space or dot.",
        "Project name contains not allowed word.",
    ]
    validations = [
        is_valid_character(name),
        is_valid_first_character(name),
        is_valid_filename(name),
    ]
    for index, error in enumerate(errors):
        if not validations[index]:
            return error
    return


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
