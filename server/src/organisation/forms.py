# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from flask_wtf import FlaskForm
from wtforms import StringField, validators, IntegerField, SelectField, BooleanField
from wtforms.validators import Optional, DataRequired
from ..forms import namespace_validation
from ..forms import IntegerListField


class CreateOrganisationForm(FlaskForm):
    """ This form is for create/update organisation """
    name = StringField('Name', [validators.Length(min=4, max=25), namespace_validation])
    description = StringField('Description', [validators.Length(max=256), Optional()])


class AccessForm(FlaskForm):
    """ Form to update access to organisation up to admin level. """
    admins = IntegerListField("Admins", [DataRequired()])
    writers = IntegerListField("Writers", [DataRequired()])
    readers = IntegerListField("Readers", [DataRequired()])


class OwnerAccessForm(AccessForm):
    owners = IntegerListField("Owners", [DataRequired()])


class UpdateOrganisationForm(FlaskForm):
    """ Form to update of organisation by owner """
    description = StringField('Description', [validators.Length(max=256), Optional()])


class OrganisationInvitationForm(FlaskForm):
    """ Form to create/update organisation invitation. """
    org_name = StringField('Organisation name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    role = SelectField('role', choices=[
        ('reader', 'reader'), ('writer', 'writer'), ('admin', 'admin'), ('owner', 'owner')])

