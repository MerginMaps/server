# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.
import pytz
from datetime import datetime, timedelta
from flask_login import current_user
from flask import current_app, abort, request

from .forms import ApiLoginForm
from ..models.db_models import Namespace
from ..auth import auth_required, authenticate
from ..auth.bearer import encode_token
from ..auth.models import User, LoginHistory
from ..auth.schemas import UserProfileSchema


def user_profile(user, return_all=True):
    """ Return user profile in json format

    Will return just some public profile if not return_all

    :param user: User data that will be returned
    :type user: User

    :return: extended user profile with mergin service info
    :rtype: dict
    """
    data = UserProfileSchema().dump(user.profile)
    data['username'] = user.username
    data['id'] = user.id

    if return_all:
        ns = Namespace.query.filter_by(name=user.username).first()
        user_disk_space = ns.disk_usage()
        data.update({
            "email": user.email,
            "disk_usage": user_disk_space,
            "storage_limit": ns.storage,
            "receive_notifications": user.profile.receive_notifications,
            "verified_email": user.verified_email,
            "tier": "free",
            "registration_date": user.profile.registration_date
        })
    return data


@auth_required
def get_user(username=None):  # noqa: E501
    """ Return user profile """
    return user_profile(current_user, return_all=True)


def _extract_first_error(errors):
    """
    For now, if the response is plain string,
    InputApp displays it in the nice
    notification window. Extract first error
    and just send that one to client
    """
    for key, value in errors.items():
        val = str(value[0])
        if key.lower() in val.lower():
            # e.g. Passwords must contain special character.
            # in this case we do not need to add key "password"
            # since it is obvious from where it comes from
            return val
        elif val.startswith("Field"):
            # e.g. Field must be longer than 4 characters
            # In this case the generic validator use Field
            # replace with the key (e.g. "Username")
            return val.replace("Field", key.capitalize())
        else:
            # show both key and value
            return val + "(" + key + ")"

    return "Unknown error in input fields"


def login():  # noqa: E501
    form = ApiLoginForm()
    if form.validate():
        user = authenticate(form.login.data, form.password.data)
        if user and user.active:
            expire = datetime.now(pytz.utc) + timedelta(seconds=current_app.config['BEARER_TOKEN_EXPIRATION'])
            token_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "expire": str(expire)
            }
            token = encode_token(current_app.config['SECRET_KEY'], token_data)

            data = user_profile(user)
            data["session"] = {
                "token": token,
                "expire": expire
            }
            LoginHistory.add_record(user.username, request)
            return data
        elif not user:
            abort(401, 'Invalid username or password')
        elif not user.active:
            abort(401, 'Account is not activated')
    abort(400, _extract_first_error(form.errors))
