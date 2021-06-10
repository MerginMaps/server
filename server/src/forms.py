# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from wtforms import StringField, Field, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_wtf import FlaskForm
from .util import is_name_allowed


def namespace_validation(form, field):
    if field.data and (not is_name_allowed(field.data) or '@' in field.data):
        raise ValidationError("Please use only alphanumeric or these -._~()'!*:,; characters in {}.".format(field.name))


class IntegerListField(Field):
    def _value(self):
        return self.data

    def process_formdata(self, valuelist):
        self.data = valuelist


class SendEmailForm(FlaskForm):
    users = IntegerListField()  # FieldList(IntegerField()) was not working
    subject = StringField(validators=[DataRequired(), Length(max=50)])
    message = StringField(validators=[DataRequired()])


class AccessPermissionForm(FlaskForm):
    permissions = SelectField("permissions", [DataRequired()], choices=[
        ('read', 'read'), ('write', 'write'), ('owner', 'owner')])
