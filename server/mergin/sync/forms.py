# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from wtforms import Field, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from mergin.sync.utils import (
    is_reserved_word,
    has_valid_characters,
    check_filename,
    has_valid_first_character,
)


def project_name_validation(name: str) -> str | None:
    """Check whether project name is valid"""
    if not name.strip():
        return "Project name cannot be empty"
    errors = [
        has_valid_characters(name),
        has_valid_first_character(name),
        is_reserved_word(name),
        check_filename(name),
    ]
    for error in errors:
        if error:
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
