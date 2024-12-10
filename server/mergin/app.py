# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import hashlib
import logging
import os
import connexion
import wtforms_json
import gevent
from marshmallow import fields
from sqlalchemy.schema import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import json, jsonify, request, abort, current_app, Flask, Request, Response
from flask_login import current_user, LoginManager
from flask_wtf.csrf import generate_csrf, CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
from connexion.apps.flask_app import FlaskJSONEncoder
from flask_wtf import FlaskForm
from wtforms import StringField
from pathlib import Path
import sys
import time
import traceback
from werkzeug.exceptions import HTTPException
from typing import List, Dict, Optional

from .sync.utils import get_blacklisted_dirs, get_blacklisted_files
from .config import Configuration

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

wtforms_json.init()
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata, engine_options={"json_serializer": json.dumps})
ma = Marshmallow()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()

this_dir = os.path.dirname(os.path.realpath(__file__))
DEPRECATION_API_MSG = (
    "Update Mergin Maps to see this information [endpoint deprecated]."
)


def traceback_hash():
    # File paths will be relative to the server directory above so hashes will be consistent across different
    # deployments
    server_root = Path(this_dir).resolve().parent

    _ty, _val, tb = sys.exc_info()  # Get traceback info
    formatted_tb = traceback.format_tb(tb)  # Format it

    # Walk backwards through the traceback and create a fingerprint for the first reference to
    # source code that's our own
    digest = ""
    formatted_tb.reverse()
    for traceback_line in formatted_tb:
        if str(server_root) in traceback_line:
            h = hashlib.sha256()
            try:
                source_file_full_path = traceback_line.split('"')[1]
                source_function = traceback_line.split(", in ")[1].split("\n")[0]
                source_line_content = traceback_line.split("\n")[-2].strip()
            except IndexError:
                logging.warning(
                    f"Failed to parse problem source info from: {traceback_line}"
                )
                break
            source_file_rel_path = os.path.relpath(source_file_full_path, server_root)
            h.update(bytes(source_file_rel_path, encoding="utf8"))
            h.update(bytes(source_function, encoding="utf8"))
            h.update(bytes(source_line_content, encoding="utf8"))
            digest = h.hexdigest()[
                :8
            ]  # The first 8 characters should be enough without filling up the logs
            break
    return digest


class InitDBError(Exception):
    pass


class UpdateForm(FlaskForm):
    """
    Base class for forms with reasonable update strategy.
    Doesn't overwrite optional fields which was not passed in data!
    """

    def update_obj(self, obj):
        from wtforms.validators import Optional

        for name, field in self._fields.items():
            is_optional = any((isinstance(v, Optional) for v in field.validators))
            # update only required fields or passed optional fields
            if not is_optional or (field.data or field.raw_data != []):
                field.populate_obj(obj, name)


class GeventTimeoutMiddleware:
    """Middleware to implement gevent.Timeout() for all requests"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        try:
            with gevent.Timeout(Configuration.GEVENT_REQUEST_TIMEOUT):
                return self.app(environ, start_response)
        except gevent.Timeout:
            logging.error(f"Gevent worker: Request {request.path} timed out")
            resp = Response("Gateway Timeout", mimetype="text/plain", status=504)
            return resp(environ, start_response)


def create_simple_app() -> Flask:
    app = connexion.FlaskApp(__name__, specification_dir=os.path.join(this_dir))
    flask_app = app.app

    flask_app.json_encoder = FlaskJSONEncoder
    flask_app.config.from_object(Configuration)
    db.init_app(flask_app)
    ma.init_app(flask_app)
    Migrate(flask_app, db)
    flask_app.connexion_app = app
    # in case of gevent worker type use middleware to implement custom request timeout
    if Configuration.GEVENT_WORKER:
        flask_app.wsgi_app = GeventTimeoutMiddleware(flask_app.wsgi_app)

    @flask_app.cli.command()
    def init_db():
        """Re-creates application database"""
        print("Database initialization ...")
        db.drop_all(bind=None)
        db.create_all(bind=None)
        db.session.commit()
        print("Done. Tables created.")

    return flask_app


def create_app(public_keys: List[str] = None) -> Flask:
    """Factory function to create Flask app instance"""
    from itsdangerous import BadTimeSignature, BadSignature
    from .auth import auth_required, decode_token
    from .auth.models import User

    # from .celery import celery
    from .sync.db_events import register_events
    from .sync.workspace import GlobalWorkspaceHandler
    from .sync.config import Configuration as SyncConfig
    from .sync.commands import add_commands
    from .auth import register as register_auth
    from .sync.project_handler import ProjectHandler

    app = create_simple_app().connexion_app

    app.add_api(
        "sync/public_api.yaml",
        arguments={"title": "Mergin"},
        options={"swagger_ui": Configuration.SWAGGER_UI},
        validate_responses=True,
    )
    app.add_api(
        "sync/public_api_v2.yaml",
        arguments={"title": "Mergin"},
        options={"swagger_ui": Configuration.SWAGGER_UI},
        validate_responses=True,
    )
    app.add_api(
        "sync/private_api.yaml",
        base_path="/app",
        arguments={"title": "Mergin"},
        options={"swagger_ui": False, "serve_spec": False},
        validate_responses=True,
    )

    app.app.config.from_object(SyncConfig)
    app.app.connexion_app = app

    mail.init_app(app.app)
    app.mail = mail
    csrf.init_app(app.app)
    login_manager.init_app(app.app)
    # register auth blueprint
    register_auth(app.app)

    # adjust login manager
    @login_manager.user_loader
    def load_user(user_id):  # pylint: disable=W0613,W0612
        return User.query.get(user_id)

    @login_manager.header_loader
    def load_user_from_header(header_val):  # pylint: disable=W0613,W0612
        if header_val.startswith("Bearer"):
            header_val = header_val.replace("Bearer ", "", 1)
            try:
                data = decode_token(
                    app.app.config["SECRET_KEY"],
                    header_val,
                    app.app.config["BEARER_TOKEN_EXPIRATION"],
                )
                user = User.query.filter_by(
                    id=data["user_id"], username=data["username"], email=data["email"]
                ).one_or_none()
                if user and user.active:
                    return user
            except (BadSignature, BadTimeSignature, KeyError):
                pass

    # csrf = app.app.extensions['csrf']

    @app.app.before_request
    def check_maintenance():
        allowed_endpoints = ["/project/by_names", "/auth/login", "/alive"]
        if (
            request.method in ["POST", "PUT", "PATCH", "DELETE"]
            and os.path.isfile(current_app.config["MAINTENANCE_FILE"])
            and all(path not in request.path for path in allowed_endpoints)
        ):
            abort(503, "Service unavailable due to maintenance, please try later")

    # Adjust CSRF policy for API
    def custom_protect():
        if request.path.startswith("/v1/") and "session" not in request.cookies:
            # Disable csrf for non-web clients
            return
        if request.path.startswith("/v2/") and "session" not in request.cookies:
            # Disable csrf for non-web clients
            return
        return csrf._protect()

    csrf._protect = csrf.protect
    csrf.protect = custom_protect

    # Cannot read csrf token from data (can be large stream)!
    # Read csrf token only from headers for API endpoints
    _get_csrf_token = csrf._get_csrf_token

    def get_csrf_token():
        if request.path.startswith("/v1/"):
            for header_name in app.app.config["WTF_CSRF_HEADERS"]:
                csrf_token = request.headers.get(header_name)
                if csrf_token:
                    return csrf_token
        return _get_csrf_token()

    csrf._get_csrf_token = get_csrf_token

    def get_startup_data():
        is_authenticated = current_user.is_authenticated and current_user.active
        data = {
            "authenticated": is_authenticated,
            "superuser": is_authenticated and current_user.is_admin,
        }
        return data

    # update celery config with flask app config
    # celery.conf.update(app.app.config)

    @app.route("/alive", methods=["POST"])
    @csrf.exempt
    def alive():  # pylint: disable=E0722
        """A more elaborate check for livliness which also ensures we can execute a database query
        Limit method to POST for detecting issues with redirected clients changing the method to GET
        """
        start_time = time.time()
        try:
            with db.engine.connect() as con:
                rs = con.execute("SELECT 2 * 2")
                assert rs.fetchone()[0] == 4
        except:
            """Although bad form, we have deliberate left this except broad. When we have an uncaught exception in
            Mergin, it results in a zombie DB connection. By missing an exception on an endpoint that will be hammered
            a lot, we could end up bringing down the service."""
            # Return a 500 and log traceback info to the server logs
            logging.error("HTTP 500: ", exc_info=True)
            abort(500)
        processing_time_ms = (time.time() - start_time) * 1000
        status = json.dumps(
            {
                "processing_time_ms": processing_time_ms,
                "maintenance": os.path.isfile(app.app.config["MAINTENANCE_FILE"]),
            }
        )
        return status, 200

    @app.route("/ping", methods=["GET"])
    def ping():  # pylint: disable=W0612
        """healthcheck and basic service info endpoint"""
        # TODO remove - it is heavily outdated
        # but first it needs to be removed from clients
        supported_endpoints = {
            "project": {
                "GET": [
                    "/project",
                    "/project/{namespace}/{project_name}",
                    "/project/version/{namespace}/{project_name}",
                ],
                "POST": [
                    "/project/{namespace}",
                    "/project/clone/{namespace}/{project_name}",
                ],
                "DELETE": ["/project/{namespace}/{project_name}"],
                "PUT": ["/project/{namespace}/{project_name}"],
            },
            "data_sync": {
                "GET": [
                    "/project/download/{namespace}/{project_name}",
                    "/project/raw/{namespace}/{project_name}",
                    "/resource/history/{namespace}/{project_name}/{file}",
                ],
                "POST": [
                    "/project/push/cancel/{transaction_id}",
                    "/project/push/finish/{transaction_id}",
                    "/project/push/{namespace}/{project_name}",
                    "/project/push/chunk/{transaction_id}/{chunk_id}",
                ],
            },
            "user": {
                "GET": ["/user/{username}"],
                "POST": ["/auth/login", "/auth/register"],
            },
        }
        status = json.dumps(
            {
                "service": "Mergin",
                "status": "online",
                "base_url": "v1",
                "endpoints": supported_endpoints,
                "version": app.app.config["VERSION"],
                "blacklist_dirs": get_blacklisted_dirs(app.app.config["BLACKLIST"]),
                "blacklist_files": get_blacklisted_files(app.app.config["BLACKLIST"]),
                "maintenance": os.path.isfile(app.app.config["MAINTENANCE_FILE"]),
                "subscriptions_enabled": app.app.config["MERGIN_SUBSCRIPTIONS"],
            }
        )
        return status, 200

    # reading raw input stream not supported in connexion so far
    # https://github.com/zalando/connexion/issues/592
    # and as workaround we use custom Flask endpoint in create_app function
    @app.route("/v1/project/push/chunk/<transaction_id>/<chunk_id>", methods=["POST"])
    @auth_required
    def chunk_upload(transaction_id, chunk_id):
        from .sync import public_api_controller

        return public_api_controller.chunk_upload(transaction_id, chunk_id)

    # if app.app.config['DEBUG']:  # pragma: no cover
    # Enable SQL debugging
    # logging.basicConfig()
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    @app.route("/app/init")  # pylint: disable=W0613,W0612
    def init():  # pylint: disable=W0612
        response = jsonify(get_startup_data())
        response.headers.set("X-CSRF-Token", generate_csrf())
        return response

    register_events()
    application = app.app

    @application.errorhandler(Exception)
    def handle_exception(e):
        """
        Based on examples here: https://flask.palletsprojects.com/en/1.1.x/errorhandling/#generic-exception-handlers
        The motivation behind this handler is to catch unhandled exceptions, so we may generate and log a unique
        fingerprint for a given bug. This will make it easier to track unique bugs.
        """

        # pass through HTTP errors
        if isinstance(e, HTTPException):
            return e

        h = traceback_hash()
        version = app.app.config["VERSION"]
        logging.error(
            f"HTTP 500: (path={request.path}|hash={h}|version={version}): ",
            exc_info=True,
        )
        abort(500)

    @application.after_request
    def log_bad_request(response):
        """Log bad requests for easier debugging"""
        if response.status_code == 400:
            if response.json.get("detail"):
                # default response from connexion (check against swagger.yaml)
                logging.warning(f'HTTP 400: {response.json["detail"]}')
            else:
                # either WTF form validation error or custom validation with abort(400)
                logging.warning(f"HTTP 400: {response.data}")
        elif response.status_code == 409:
            # request which would result in conflict, e.g. creating the same project again
            logging.warning(f"HTTP 409: {response.data}")
        elif response.status_code == 422:
            # request was valid but still could not be processed, e.g. limits error
            logging.info(f"HTTP 422: {response.data}", exc_info=True)
        else:
            # ignore other errors
            pass

        return response

    @application.after_request
    def set_custom_error_header(response):
        """Clients (e.g. plugin) expect error `Content-Type` in response header.
        Some responses with custom error lacks it."""
        if response.status_code == 422:
            response.headers["Content-Type"] = "application/problem+json"

        return response

    # we need to register default handler to be accessible within app
    application.ws_handler = GlobalWorkspaceHandler()
    application.project_handler = ProjectHandler()

    # append config route with settings from app.config needed by clients
    if public_keys:

        @app.route("/config")
        def config():
            cfg = {key.lower(): application.config.get(key) for key in public_keys}
            cfg["blacklist_dirs"] = get_blacklisted_dirs(
                application.config["BLACKLIST"]
            )
            cfg["blacklist_files"] = get_blacklisted_files(
                application.config["BLACKLIST"]
            )
            cfg["version"] = application.config["VERSION"]
            parsed_version = parse_version_string(application.config["VERSION"])
            if parsed_version:
                cfg = {**cfg, **parsed_version}

            cfg["server_configured"] = is_server_configured()
            cfg["build_hash"] = application.config["BUILD_HASH"]
            return jsonify(cfg), 200

    # append project commands (from default sync module)
    add_commands(application)
    return application


class DateTimeWithZ(fields.DateTime):
    def __init__(self, **kwargs):
        super(DateTimeWithZ, self).__init__("%Y-%m-%dT%H:%M:%S%zZ", **kwargs)


def parse_version_string(version: str) -> Optional[Dict]:
    """Parse version string in format XXXX.Y.Z"""
    ver_parts = version.split(".")
    try:
        if len(ver_parts) == 3:
            fix = int(ver_parts[2])
        else:
            fix = None
        version = {"major": int(ver_parts[0]), "minor": int(ver_parts[1]), "fix": fix}
        return version
    except ValueError:
        return None


def is_server_configured():
    """Validate server is configured correctly for deployment"""
    return current_app.config.get("MERGIN_BASE_URL", "") != ""


class ResponseError:
    """Base class for custom error messages"""

    code = "BaseError"
    detail = "Request failed"

    def to_dict(self) -> Dict:
        return dict(code=self.code, detail=self.detail + f" ({self.code})")


def whitespace_filter(obj):
    return obj.strip() if isinstance(obj, str) else obj


class CustomStringField(StringField):
    """Custom class for string form fields"""

    def __init__(self, *args, **kwargs):
        filters = kwargs.get("filters")
        # add whitespace filter
        kwargs["filters"] = (
            (*filters, whitespace_filter) if filters else (whitespace_filter,)
        )
        super().__init__(*args, **kwargs)
