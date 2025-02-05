import click
from flask import Flask
import random
import string
from datetime import datetime, timezone


def _echo_title(title):
    click.echo("")
    click.echo(f"# {title}")
    click.echo()


def _echo_error(msg):
    click.secho("Error: ", fg="red", nl=False, bold=True)
    click.secho(msg, fg="bright_red")


def add_commands(app: Flask):
    from .app import db
    from mergin.auth.models import UserProfile

    def _check_celery():
        from celery import current_app

        ping_celery = current_app.control.inspect().ping()
        if not ping_celery:
            _echo_error(
                "Celery process not running properly. Configure celery worker and celery beat. This breaks also email sending from the system.",
            )
            return
        click.secho("Celery is running properly", fg="green")
        return True

    def _send_statistics():
        from .stats.tasks import send_statistics

        if not app.config.get("COLLECT_STATISTICS"):
            return

        _echo_title("Sending statistics.")
        if not _check_celery():
            return
        send_statistics.delay()
        click.secho("Statistics sent.", fg="green")

    def _send_email(email: str):
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
        except Exception as e:
            _echo_error(
                f"Error sending email: {e}",
            )

    def _check_server():  # pylint: disable=W0612
        """Check server configuration."""

        _echo_title("Server health check")
        click.echo(f"Mergin Maps version: {app.config['VERSION']}")

        base_url = app.config["MERGIN_BASE_URL"]
        if not base_url:
            _echo_error(
                "No base URL set. Please set MERGIN_BASE_URL environment variable",
            )
        else:
            click.secho(f"Base URL of server is {base_url}", fg="green")

        tables = db.engine.table_names()
        if not tables:
            _echo_error("Database not initialized. Run flask init-db command")
        else:
            click.secho("Database initialized properly", fg="green")

        _check_celery()

    def _init_db():
        """Create database tables."""
        from .stats.models import MerginInfo

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

    @app.cli.command()
    def init_db():
        """Re-create database tables."""
        _init_db()

    @app.cli.command()
    @click.option("--email", "-e", required=True)
    @click.option(
        "--recreate",
        "-r",
        help="Recreate database and admin user.",
        is_flag=True,
        required=False,
    )
    def init(email: str, recreate: bool):
        """Initialize database if does not exist or -r is provided. Perform check of server configuration. Send statistics, respecting your setup."""

        from .auth.models import User

        tables = db.engine.table_names()
        if not tables or recreate:
            _init_db()

            _echo_title("Creating admin user. Copy generated password.")
            username = "admin"
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
            click.secho(f"Username: {username}")
            click.secho(f"Password: {password}")
            click.secho(f"Email: {email}")
        _check_server()
        _send_email(email)
        _send_statistics()

    @app.cli.group()
    def server():
        """Server management commands."""
        pass

    @server.command()
    @click.option("--email", required=True)
    def send_check_email(email: str):  # pylint: disable=W0612
        """Send check email to specified email address."""
        _send_email(email)

    @server.command()
    def check():
        """Check server configuration."""
        _check_server()
