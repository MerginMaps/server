# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import logging
import os
from operator import and_

import connexion
from sqlalchemy.schema import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import json, jsonify, render_template, send_from_directory, request, abort, url_for, current_app
from flask_login import current_user
from flask_wtf.csrf import generate_csrf
from flask_migrate import Migrate
from flask_mail import Mail
import wtforms_json
from sqlalchemy import desc, asc, or_

from . import encoder
from .forms import SendEmailForm, AccessPermissionForm
from .mergin_utils import get_blacklisted_dirs, get_blacklisted_files
from .webhooks import WebhookManager, Webhook


class PostgresAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        options.update({
            'json_serializer': json.dumps
        })
        super(PostgresAlchemy, self).apply_driver_hacks(app, info, options)


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

wtforms_json.init()
metadata = MetaData(naming_convention=convention)
db = PostgresAlchemy(metadata=metadata)
ma = Marshmallow()
mail = Mail()
wm = WebhookManager()

# signals
SIG_NEW_PROJECT = 'new-project'
SIG_NEW_USER = 'new-user'
SIG_DELETED_USER = 'deleted-user'
SIG_PROJECT_TRANSFERED = 'project-transferred'
SIG_NEW_ORGANISATION = 'new-organisation'
SIG_DELETED_ORGANISATION = 'deleted-organisation'


class SlackWebhook(Webhook):
    """ Class for sending notifications to Slack """

    def __init__(self):
        slack_url = os.environ.get('SLACK_HOOK_URL', '')
        super().__init__('Slack', slack_url)

    def format_data(self, data):
        # check this for reference https://api.slack.com/messaging/composing/formatting#basics
        return {'text': data}


this_dir = os.path.dirname(os.path.realpath(__file__))

class InitDBError(Exception):
    pass


def create_app():
    from .permissions import require_project, ProjectPermissions
    from .models.db_models import Project, ProjectAccess, ProjectVersion, Namespace, ProjectTransfer, Upload, Account, RemovedProject
    from .models.schemas import ProjectSchema, ProjectListSchema, RemovedProjectSchema
    from .config import Configuration
    from .auth import auth_required, init_app
    from .auth.models import User, UserProfile
    from .auth.schemas import UserSchema
    from .controllers import project_controller
    from .celery import celery, send_email_async
    from .organisation import init_app
    from .organisation.models import Organisation, OrganisationInvitation
    from .db_events import register_events
    from .storages.disk import move_to_tmp

    app = connexion.FlaskApp(__name__, specification_dir=os.path.join(this_dir, os.pardir))
    app.app.json_encoder = encoder.JSONEncoder

    api_options = {"swagger_ui": Configuration}
    app.add_api('swagger.yaml', arguments={'title': 'Mergin'}, options=api_options)

    app.app.config.from_object(Configuration)

    db.init_app(app.app)
    ma.init_app(app.app)
    auth.init_app(app.app)
    Migrate(app.app, db)
    mail.init_app(app.app)
    organisation.init_app(app.app)

    slack = SlackWebhook()
    # register and connect some basic signals
    signals = [SIG_NEW_USER, SIG_DELETED_USER, SIG_NEW_PROJECT]
    for signal in signals:
        wm.register_signal(signal)
        wm.connect_handler(signal, slack)

    # Adjust CSRF policy for API
    csrf = app.app.extensions['csrf']

    @app.app.before_request
    def check_maintenance():
        allowed_endpoinds = ["/project/by_names", "/auth/login"]
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and os.path.isfile(current_app.config['MAINTENANCE_FILE']) and all(path not in request.path for path in allowed_endpoinds):
            abort(503, "Service unavailable due to maintenance, please try later")

    def custom_protect():
        if request.path.startswith('/v1/') and 'session' not in request.cookies:
            # Disable csrf for non-web clients
            return
        return csrf._protect()

    csrf._protect = csrf.protect
    csrf.protect = custom_protect

    # Cannot read csrf token from data (can be large stream)!
    # Read csrf token only from headers for API endpoints
    _get_csrf_token = csrf._get_csrf_token

    def get_csrf_token():
        if request.path.startswith('/v1/'):
            for header_name in app.app.config['WTF_CSRF_HEADERS']:
                csrf_token = request.headers.get(header_name)
                if csrf_token:
                    return csrf_token
        return _get_csrf_token()

    csrf._get_csrf_token = get_csrf_token

    def get_startup_data():
        from .organisation import find_organisations_by_username, OrganisationSchema

        data = {
            "version": app.app.config['VERSION']
        }
        if current_user.is_authenticated and current_user.active:
            schema = UserSchema()
            data["user"] = schema.dump(current_user)
            organisations = find_organisations_by_username(current_user.username)
            data['organisations'] = OrganisationSchema(many=True, context={"user": current_user}).dump(organisations)
            projects_count = Project.query.filter(Project.creator_id == current_user.id).filter_by(namespace=current_user.username).count()
            data["user"]["has_project"] = True if projects_count > 0 else False
        if app.app.config["USER_SELF_REGISTRATION"]:
            data["registration"] = url_for('auth.self_register_user')
        return data

    # update celery config with flask app config
    celery.conf.update(app.app.config)

    @app.route("/assets/<path:filename>")
    def send_asset(filename):  # pylint: disable=W0612
        return send_from_directory(app.app.config["PUBLIC_DIR"], filename)  # pragma: no cover

    def web_app(path=None):  # pylint: disable=W0613,W0612  # pragma: no cover
        """ Default view function to render vue application """
        data = get_startup_data()
        data['csrf'] = generate_csrf()
        return render_template("app.html", data=data)

    # register frontend routes as flask default view endpoint
    rules = [
        '/', '/signup', '/login', '/login/<path:path>', '/users', '/users/<path:path>', '/projects',
        '/projects/<path:path>', '/organisations', '/organisations/<path:path>', '/profile', '/dashboard'
    ]
    for rule in rules:
        app.add_url_rule(rule, 'web_app', web_app, methods=["GET"])

    @app.route('/admin', methods=['GET'])
    @app.route('/admin/<path:path>', methods=['GET'])
    @auth_required(permissions=['admin'])
    def admin_web_app(path=None):  # pylint: disable=W0613,W0612  # pragma: no cover
        data = get_startup_data()
        data['csrf'] = generate_csrf()
        return render_template("app.html", data=data)

    @app.route('/ping', methods=['GET'])
    def ping():  # pylint: disable=W0612
        """ healthcheck and basic service info endpoint """
        supported_endpoints = {
            "project": {
                "GET": [
                    "/project", "/project/{namespace}/{project_name}",
                    "/project/version/{namespace}/{project_name}"
                ],
                "POST": [
                    "/project/{namespace}",
                    "/project/clone/{namespace}/{project_name}"
                ],
                "DELETE": [
                    "/project/{namespace}/{project_name}"
                ],
                "PUT": [
                    "/project/{namespace}/{project_name}"
                ]
            },
            "data_sync": {
                "GET": [
                    "/project/download/{namespace}/{project_name}",
                    "/project/raw/{namespace}/{project_name}",
                    "/resource/history/{namespace}/{project_name}/{file}"
                ],
                "POST": [
                    "/project/push/cancel/{transaction_id}",
                    "/project/push/finish/{transaction_id}",
                    "/project/push/{namespace}/{project_name}",
                    "/project/push/chunk/{transaction_id}/{chunk_id}"
                ]
            },
            "user": {
                "GET": [
                    "/user/{username}"
                ],
                "POST": [
                    "/auth/login",
                    "/auth/register"
                ]
            }
        }
        status = json.dumps({
            "service": "Mergin",
            "status": "online",
            "base_url": "v1",
            "endpoints": supported_endpoints,
            "version": app.app.config['VERSION'],
            "blacklist_dirs": get_blacklisted_dirs(app.app.config['BLACKLIST']),
            "blacklist_files": get_blacklisted_files(app.app.config['BLACKLIST']),
            "maintenance": os.path.isfile(app.app.config['MAINTENANCE_FILE']),
            "subscriptions_enabled": app.app.config["MERGIN_SUBSCRIPTIONS"]
        })
        return status, 200

    # reading raw input stream not supported in connexion so far
    # https://github.com/zalando/connexion/issues/592
    # and as workaround we use custom Flask endpoint in create_app function
    @app.route('/v1/project/push/chunk/<transaction_id>/<chunk_id>', methods=['POST'])
    @auth_required
    def chunk_upload(transaction_id, chunk_id):
        return project_controller.chunk_upload(transaction_id, chunk_id)

    @app.route('/app/project/access_request/<namespace>/<project_name>', methods=['POST'])
    @auth_required
    def create_project_access_request(namespace, project_name):  # noqa: E501
        from src.models.db_models import AccessRequest
        if not current_user.active:
            return "You are not active anymore", 409

        project = Project.query.filter(Project.name == project_name, Project.namespace == namespace).first_or_404()
        if current_user.id in project.access.readers:
            return "You already have access to project", 409

        access_request = AccessRequest.query.filter_by(namespace=namespace, project_id=project.id, user_id=current_user.id).first()
        if access_request:
            return "Project access request already exists", 409

        access_request = AccessRequest(project, current_user.id)
        db.session.add(access_request)
        db.session.commit()
        # notify project owners
        owners = User.query.join(UserProfile)\
            .filter(User.verified_email, User.id.in_(project.access.owners))\
            .filter(UserProfile.receive_notifications)\
            .all()
        for owner in owners:
            email_data = {
                "subject": "Project access requested",
                "html": render_template(
                    "email/project_access_request.html",
                    expire=access_request.expire,
                    link=f"{request.url_root.rstrip('/')}/projects/{project.namespace}/{project.name}/settings",
                    user=current_user.username, username=owner.username,
                    project_name=f"{project.namespace}/{project.name}"
                ),
                "recipients": [owner.email],
                "sender": app.app.config['MAIL_DEFAULT_SENDER']
            }
            send_email_async.delay(**email_data)
        return "", 200

    @app.route('/app/project/access_request/<request_id>', methods=['DELETE'])
    @auth_required
    def delete_project_access_request(request_id):  # noqa: E501
        from .models.db_models import AccessRequest
        access_request = AccessRequest.query.get_or_404(request_id)
        if current_user.id in access_request.project.access.owners \
                or current_user.id == access_request.project.creator \
                or current_user.id == access_request.user_id:
            AccessRequest.query.filter(AccessRequest.id == request_id).delete()
            db.session.commit()
            return "", 200
        else:
            return "You don't have permissions to remove project access request", 403

    @app.route('/app/project/accept/request/<request_id>', methods=['POST'])
    @auth_required
    def accept_project_access_request(request_id):
        from .models.db_models import AccessRequest

        form = AccessPermissionForm()
        if form.validate():
            permission = form.permissions.data
            access_request = AccessRequest.query.get_or_404(request_id)
            if current_user.id in access_request.project.access.owners or current_user.id == access_request.project.creator:
                access_request.accept(permission)
                return "", 200
            else:
                return "You don't have permissions to accept project access request", 403
        else:
            return jsonify(form.errors), 400

    @app.route('/app/project/access_requests', methods=['GET'])
    @auth_required
    def get_project_access_requests():
        from .models.db_models import AccessRequest
        from .models.schemas import ProjectAccessRequestSchema

        access_requests = AccessRequest.query.filter((AccessRequest.user_id == current_user.id) | (AccessRequest.namespace == current_user.username)).all()
        return jsonify(ProjectAccessRequestSchema(many=True).dump(access_requests)), 200

    @app.route('/app/removed-project', methods=['GET'])
    @auth_required(permissions=['admin'])
    def paginate_removed_projects():  # noqa: E501
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        order_by = request.args.get('order_by', None)
        descending = str(request.args.get('descending', 'false')) == 'true'

        projects = RemovedProject.query
        if descending and order_by:
            projects = projects.order_by(desc(RemovedProject.__table__.c[order_by]))
        elif not descending and order_by:
            projects = projects.order_by(asc(RemovedProject.__table__.c[order_by]))
        result = projects.paginate(page, per_page).items
        total = projects.paginate(page, per_page).total
        data = RemovedProjectSchema(many=True).dump(result)
        data = {'projects': data, 'count': total}
        return data, 200

    @app.route('/app/removed-project/restore/<id>', methods=['POST'])
    @auth_required(permissions=['admin'])
    def restore_project(id):  # noqa: E501
        rp = RemovedProject.query.get_or_404(id)
        project_name = f"{rp.namespace}/{rp.name}"
        project = Project.query.filter(or_(and_(Project.name == rp.name, Project.namespace == rp.namespace), Project.id == rp.properties["id"] )).first()
        if project:
            abort(409, f"Failed to restore: project {project_name} already exists")

        creator = User.query.get(rp.properties['creator_id'])
        if not (creator and creator.active):
            abort(400, f"Failed to restore: creator of project {project_name} is not available")

        # create new project, restore metadata and recreate project versions
        p = Project(rp.name, rp.properties["storage_params"], creator, rp.namespace)
        for attr in ("id", "created", "updated", "files", "tags", "disk_usage", "latest_version"):
            setattr(p, attr, rp.properties.get(attr))
        p.access = ProjectAccess(p, public=False)
        db.session.add(p)
        for version in rp.properties["versions"]:
            pv = ProjectVersion(p, version["name"], version["author"], version["changes"],
                                version["files"], version["ip_address"], version["user_agent"])
            pv.created = version["created"]
            pv.ip_geolocation_country = version["ip_geolocation_country"]
            db.session.add(pv)
        db.session.delete(rp)
        db.session.commit()
        return "", 201

    @app.route('/app/removed-project/<id>', methods=['DELETE'])
    @auth_required(permissions=['admin'])
    def retire_removed_project(id):  # noqa: E501
        rp = RemovedProject.query.get_or_404(id)
        db.session.add(rp)
        db.session.delete(rp)
        db.session.commit()
        rp_dir = os.path.abspath(os.path.join(current_app.config['LOCAL_PROJECTS'], rp.properties["storage_params"]["location"]))
        if os.path.exists(rp_dir):
            move_to_tmp(rp_dir)
        return "", 204

    @app.route('/app/templates', methods=['GET'])
    @auth_required
    def template_projects():  # pylint: disable=W0612
        projects = Project.query.filter(Project.creator.has(username='TEMPLATES')).all()
        project_schema = ProjectListSchema(many=True)
        return jsonify(project_schema.dump(projects)), 200

    @app.route('/app/email_notification', methods=['POST'])
    @auth_required(permissions=['admin'])
    def send_email_notification():
        """
        Send email composed in web UI to all selected users as BCC.
        """
        form = SendEmailForm()
        if form.validate():
            users = User.query.join(
                UserProfile).filter(User.verified_email,
                User.username.in_(form.users.data)).filter(
                UserProfile.receive_notifications).all()
            if not users:
                return jsonify({"success": True})

            email_data = {
                'subject': form.subject.data,
                'html': form.message.data,
                'recipients': [app.app.config['MAIL_DEFAULT_SENDER']],
                'bcc': [user.email for user in users],
                'sender': app.app.config['MAIL_DEFAULT_SENDER']
            }
            send_email_async.delay(**email_data)
            return jsonify({"success": True})
        return jsonify(form.errors), 404

    if app.app.config['DEBUG']:  # pragma: no cover
        @app.route("/dev/init")  # pylint: disable=W0613,W0612
        def init():  # pylint: disable=W0612
            response = jsonify(get_startup_data())
            response.headers.set('X-CSRF-Token', generate_csrf())
            return response

        # Enable SQL debugging
        # logging.basicConfig()
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    register_events()
    application = app.app

    # REGISTER BLUEPRINTS
    from .controllers.account_controller import account
    application.register_blueprint(account, url_prefix='/app')

    @application.after_request
    def log_bad_request(response):
        """ Log bad requests for easier debugging """
        if response.status_code == 400:
            if response.json.get("detail"):
                # default response from connexion (check against swagger.yaml)
                logging.warning(f'HTTP 400: {response.json["detail"]}')
            else:
                # either WTF form validation error or custom validation with abort(400)
                logging.warning(f'HTTP 400: {response.data}')
        elif response.status_code == 409:
            # request which would result in conflict, e.g. creating the same project again
            logging.warning(f'HTTP 409: {response.data}')
        elif response.status_code == 422:
            # request was valid but still could not be processed, e.g. geodiff error
            logging.error(f'HTTP 422: {response.data}', exc_info=True)
        else:
            # ignore other errors
            pass

        return response

    return application
