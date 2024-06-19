# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import click
from flask import Flask
from sqlalchemy import or_, func

from .. import db
from .models import User, UserProfile


def add_commands(app: Flask):
    @app.cli.group()
    def user():
        """User management commands."""
        pass

    @user.command()
    @click.argument("username")
    @click.argument("password")
    @click.option("--is-admin", is_flag=True)
    @click.option("--email", required=True)
    def create(username, password, is_admin, email):  # pylint: disable=W0612
        """Create user account"""
        user = User.query.filter(
            or_(
                func.lower(User.username) == func.lower(username),
                func.lower(User.email) == func.lower(email),
            )
        ).first()
        if user:
            print("ERROR: User already exists!\n")
            return

        user = User(username=username, passwd=password, is_admin=is_admin, email=email)
        user.profile = UserProfile()
        user.active = True
        db.session.add(user)
        db.session.commit()
