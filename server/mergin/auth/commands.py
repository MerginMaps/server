# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import sys
import click
from flask import Flask
from sqlalchemy import or_, func

from ..app import db
from .models import User, UserProfile
from ..commands import normalize_input


def add_commands(app: Flask):
    @app.cli.group()
    def user():
        """User management commands."""
        pass

    @user.command()
    @click.argument("username", callback=normalize_input())
    @click.argument("password")
    @click.option("--is-admin", is_flag=True)
    @click.option("--email", required=True, callback=normalize_input())
    def create(username, password, is_admin, email):  # pylint: disable=W0612
        """Create user account"""
        user = User.query.filter(
            or_(
                func.lower(User.username) == username,
                func.lower(User.email) == email,
            )
        ).count()
        if user:
            click.secho("ERROR: User already exists", fg="red", err=True)
            sys.exit(1)

        user = User(username=username, passwd=password, is_admin=is_admin, email=email)
        user.profile = UserProfile()
        user.active = True
        db.session.add(user)
        db.session.commit()
        click.secho("User created", fg="green")
