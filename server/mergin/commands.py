import click
from flask import Flask
from sqlalchemy import or_, func


from .config import Configuration


def add_commands(app: Flask):
    from .app import db

    @app.cli.group()
    def server():
        """Server management commands."""
        pass

    @server.command()
    @click.option("--email", required=False)
    def check(email: str):  # pylint: disable=W0612
        """Check server configuration. Define email to send testing email."""
        from celery import current_app
        from mergin.celery import send_email

        click.echo(f"Mergin Maps server version: {app.config['VERSION']}")

        base_url = app.config["MERGIN_BASE_URL"]
        if not base_url:
            click.echo(
                click.style(
                    "No base URL set. Please set MERGIN_BASE_URL environment variable",
                    fg="red",
                ),
            )
        else:
            click.echo(f"Base URL of server is {base_url}")

        tables = db.engine.table_names()
        if not tables:
            click.echo(
                click.style(
                    "Database not initialized. Run flask init-db command", fg="red"
                )
            )
        else:
            click.echo("Database initialized properly")

        ping_celery = current_app.control.inspect().ping()
        if not ping_celery:
            click.echo(
                click.style(
                    "Celery not running. Configure celery worker and celery beat",
                    fg="red",
                )
            )
        else:
            click.echo("Celery running properly")

        if email:
            if not app.config["MAIL_DEFAULT_SENDER"]:
                click.echo(
                    click.style(
                        "No default sender set. Please set MAIL_DEFAULT_SENDER environment variable",
                        fg="red",
                    )
                )
                return
            email_data = {
                "subject": "Mergin Maps server check",
                "html": "Awesome, your email congiruration of Mergin Maps server is working.",
                "recipients": [email],
                "sender": app.config["MAIL_DEFAULT_SENDER"],
            }
            click.echo(
                f"Sending email to specified email address {email}. Check your inbox."
            )
            try:
                send_email(**email_data)
            except Exception as e:
                click.echo(
                    click.style(
                        f"Error sending email: {e}",
                        fg="red",
                    )
                )
