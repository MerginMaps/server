# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import click
from flask import Flask
import random
import string
import os


def _echo_title(title):
    click.echo("")
    click.echo(f"# {title}")
    click.echo()


def _echo_error(msg):
    click.secho("Error: ", fg="red", nl=False, bold=True)
    click.secho(msg, fg="bright_red")


def _check_celery() -> bool:
    from celery import current_app

    ping_celery = current_app.control.inspect().ping()
    if not ping_celery:
        _echo_error(
            "Celery process not running properly. Configure celery worker and celery beat. This breaks also email sending from the system.",
        )
        return False
    click.secho("Celery is running properly", fg="green")
    return True


def _send_statistics(app: Flask):
    from .stats.tasks import send_statistics, save_statistics

    _echo_title("Sending statistics.")
    # save rows to MerginStatistics table
    save_statistics.delay()

    if not app.config.get("COLLECT_STATISTICS"):
        click.secho(
            "Statistics sending is disabled.",
        )
        return

    if not _check_celery():
        return
    send_statistics.delay()
    click.secho("Statistics sent.", fg="green")


def _send_email(app: Flask, email: str):
    """Send check email to specified email address."""
    from .celery import send_email_async

    _echo_title(f"Sending check email to specified email address {email}.")
    if app.config["MAIL_SUPPRESS_SEND"]:
        _echo_error(
            "Sending emails is disabled. Please set MAIL_SUPPRESS_SEND=False to enable sending emails."
        )
        return
    default_sender = app.config.get("MAIL_DEFAULT_SENDER")
    if not default_sender:
        _echo_error(
            "No default sender set. Please set MAIL_DEFAULT_SENDER environment variable",
        )
        return
    email_data = {
        "subject": "Mergin Maps server check",
        "html": "Awesome, your email configuration of Mergin Maps server is working.",
        "recipients": [email],
        "sender": default_sender,
    }
    try:
        is_celery_running = _check_celery()
        if not is_celery_running:
            return
        send_email_async.delay(**email_data)
        click.secho("Email sent.", fg="green")
    except Exception as e:
        _echo_error(
            f"Error sending email: {e}",
        )


def _check_permissions(path):
    """Check for write permission on working folders"""

    if not os.access(path, os.W_OK):
        _echo_error(
            f"Permissions for {path} folder not set correctly. Please review these settings.",
        )
    else:
        click.secho(f"Permissions granted for {path} folder.", fg="green")


def _check_server(app: Flask):  # pylint: disable=W0612
    """Check server configuration."""
    from .stats.models import MerginInfo
    from .app import db

    _echo_title("Server health check")
    edition_map = {
        "ce": "Community Edition",
        "ee": "Enterprise Edition",
    }
    edition = edition_map.get(app.config["SERVER_TYPE"])
    if edition:
        click.echo(f"Mergin Maps edition: {edition}")
    click.echo(f"Mergin Maps version: {app.config['VERSION']}")

    base_url = app.config["MERGIN_BASE_URL"]
    if not base_url:
        _echo_error(
            "No base URL set. Please set MERGIN_BASE_URL environment variable",
        )
    else:
        click.secho(f"Base URL of server is {base_url}", fg="green")

    contact_email = app.config["CONTACT_EMAIL"]
    if not contact_email:
        _echo_error(
            "No contact email set. Please set CONTACT_EMAIL environment variable",
        )
    else:
        click.secho(f"Your contact email is {contact_email}.", fg="green")

    info = MerginInfo.query.first()
    service_id = app.config.get("SERVICE_ID") or (info.service_id if info else None)

    if service_id:
        click.secho(f"Service ID is {service_id}.", fg="green")
    else:
        _echo_error("No service ID set.")

    tables = db.engine.table_names()
    if not tables:
        _echo_error("Database not initialized. Run flask init-db command")
    else:
        click.secho("Database initialized properly", fg="green")

    _check_permissions(app.config.get("LOCAL_PROJECTS"))

    _check_celery()


def _init_db(app: Flask):
    """Create database tables."""
    from .stats.models import MerginInfo
    from .app import db

    _echo_title("Database initialization")
    with click.progressbar(
        label="Creating database", length=4, show_eta=False
    ) as progress_bar:
        progress_bar.update(0)
        db.drop_all(bind=None)
        progress_bar.update(1)
        db.create_all(bind=None)
        progress_bar.update(2)
        db.session.commit()
        progress_bar.update(3)
        info = MerginInfo.query.first()
        if not info and app.config.get("COLLECT_STATISTICS"):
            # create new info with random service id
            service_id = app.config.get("SERVICE_ID", None)
            info = MerginInfo(service_id)
            db.session.add(info)
            db.session.commit()
        progress_bar.update(4)

    click.secho("Tables created.", fg="green")


def add_commands(app: Flask):
    from .app import db

    @app.cli.command()
    def init_db():
        """Re-create database tables."""
        _init_db(app)

    @app.cli.command()
    @click.option("--email", "-e", required=True, envvar="CONTACT_EMAIL")
    @click.option(
        "--recreate",
        "-r",
        help="Recreate database and admin user.",
        is_flag=True,
        required=False,
    )
    def init(email: str, recreate: bool):
        """Initialize database if does not exist or -r is provided. Perform check of server configuration. Send statistics, respecting your setup."""
        from mergin.auth.models import UserProfile
        from .auth.models import User

        tables = db.engine.table_names()
        if recreate and tables:
            click.confirm(
                "Are you sure you want to recreate database and admin user? This will remove all data!",
                default=False,
                abort=True,
            )

        if not tables or recreate:
            _init_db(app)

            _echo_title("Creating admin user. Copy generated password.")
            username = User.generate_username(email)
            password_chars = string.ascii_letters + string.digits
            password = "".join(random.choice(password_chars) for i in range(12))
            user = User(username=username, passwd=password, email=email, is_admin=True)
            user.profile = UserProfile()
            user.active = True
            db.session.add(user)
            db.session.commit()
            click.secho(
                "Admin user created. Please save generated password.", fg="green"
            )
            click.secho(f"Email: {email}")
            click.secho(f"Username: {username}")
            click.secho(f"Password: {password}")
        _check_server(app)
        _send_email(app, email)
        _send_statistics(app)

    @app.cli.group()
    def server():
        """Server management commands."""
        pass

    @server.command()
    @click.option("--email", required=True, callback=normalize_input())
    def send_check_email(email: str):  # pylint: disable=W0612
        """Send check email to specified email address."""
        _send_email(app, email)

    @server.command()
    def check():
        """Check server configuration."""
        _check_server(app)

    @server.command()
    @click.option("--path", required=False, default=app.config.get("LOCAL_PROJECTS"))
    def permissions(path: str):
        """Check for specific path write permission"""
        _check_permissions(path)

    @server.command()
    def send_statistics():
        """Send usage statistics"""
        _send_statistics(app)


def normalize_input(lowercase=True, strip=True):
    def _normalize(ctx, param, value):
        if value is None:
            return value
        if strip:
            value = value.strip()
        if lowercase:
            value = value.lower()
        return value

    return _normalize
