# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import safe
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import StringField, PasswordField, BooleanField, FormField, validators, IntegerField, SelectField
from wtforms.validators import DataRequired, Optional, Length, ValidationError, Email, EqualTo
from wtforms.compat import iteritems

from ..forms import namespace_validation
from .models import User


def whitespace_filter(obj):
    return obj.strip() if isinstance(obj, str) else obj


class UpdateForm(FlaskForm):
    """
    Base class for forms with reasonable update strategy.
    Doesn't overwrite optional fields which was not passed in data!
    """
    def update_obj(self, obj):
        for name, field in iteritems(self._fields):
            is_optional = any((isinstance(v, Optional) for v in field.validators))
            # update only required fields or passed optional fields
            if not is_optional or (field.data or field.raw_data != []):
                field.populate_obj(obj, name)


class PasswordValidator():

    def __init__(self, min_length=8):
        self.min_length = min_length

    def __call__(self, form, field):
        if len(field.data) < self.min_length:
            raise ValidationError("Passwords must be at least {} characters long.".format(self.min_length))

        strength = safe.check(field.data, self.min_length)
        if not bool(strength):
            raise ValidationError('Password is not strong enough')


class LoginForm(FlaskForm):
    """ Form with username and password fields for user to sign in. """
    login = StringField(validators=[DataRequired(), Length(max=80)])
    password = PasswordField(validators=[DataRequired()])


class RegisterUserForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[validators.Length(min=4, max=25), namespace_validation],
        filters=(whitespace_filter, )
    )
    email = StringField(
        'Email Address',
        validators=[DataRequired(), Email()],
        filters=(whitespace_filter, )
    )

    def validate(self):
        if not super().validate():
            return False

        # check for existence in Namespace table
        from ..models.db_models import Namespace
        ns = Namespace.query.filter(func.lower(Namespace.name) == func.lower(self.username.data.strip())).first()
        if ns:
            self.username.errors.append("Already exists")
            return False
        user = User.query.filter(
            (func.lower(User.username) == func.lower(self.username.data.strip())) |
            (func.lower(User.email) == func.lower(self.email.data.strip()))).first()
        if user:
            if user.username.lower() == self.username.data.lower().strip():
                self.username.errors.append("Already exists")
            if user.email.lower() == self.email.data.lower().strip():
                self.email.errors.append("Already exists")
            return False
        return True


class ResetPasswordForm(FlaskForm):
    email = StringField('Email Address', [DataRequired(), Email()], filters=(whitespace_filter, ))


class UserPasswordForm(FlaskForm):
    password = PasswordField(
        'Password',
        [DataRequired(), PasswordValidator(min_length=8)]
    )
    confirm = PasswordField('Confirm password', [
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])


class UserRegistrationForm(RegisterUserForm, UserPasswordForm):
    pass


class UserChangePasswordForm(UserPasswordForm):
    old_password = StringField(
        'Old Password', [DataRequired()])


class UserForm(UpdateForm):
    is_admin = BooleanField('Admin', [Optional()])
    active = BooleanField('Active', [Optional()])


class UserProfileDataForm(UpdateForm):
    """ This form is for user profile update """
    receive_notifications = BooleanField(
        'Receive notifications', [Optional()])
    first_name = StringField('First Name', [Optional()], filters=(whitespace_filter, ))
    last_name = StringField('Last Name', [Optional()], filters=(whitespace_filter, ))
    email = StringField('Email', [Optional(), Email()], filters=(whitespace_filter, ))
