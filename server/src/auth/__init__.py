# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import functools
import os
from datetime import datetime, timedelta

from flask import request, current_app, jsonify, url_for, render_template, redirect, abort, Blueprint
from flask_login import LoginManager, login_user, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadTimeSignature
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func

from .models import User, UserProfile, LoginHistory
from .schemas import UserSchema, UserSearchSchema, AccountSearchSchema
from .forms import (LoginForm, RegisterUserForm, UserPasswordForm, ResetPasswordForm,
                    UserRegistrationForm, UserForm, UserProfileDataForm, UserChangePasswordForm)
from .bearer import decode_token
from .. import db, wm, SIG_NEW_USER, SIG_DELETED_USER

_permissions = {}
def register_permission(name, fn):
    _permissions[name] = fn

register_permission('admin', lambda user: user.is_admin)


def auth_required(f=None, permissions=None):
    if f is None:
        if permissions:
            permissions_fn = []
            for name in permissions:
                if name not in _permissions:
                    raise KeyError('Unknown permission: {}'.format(name))
                permissions_fn.append(_permissions[name])
        return functools.partial(auth_required, permissions=permissions_fn)

    @functools.wraps(f)
    def wrapped_func(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return 'Authentication information is missing or invalid.', 401
        if permissions:
            for check_permission in permissions:
                if not check_permission(current_user):
                    return 'Permission denied.', 403
        return f(*args, **kwargs)
    return wrapped_func


def authenticate(login, password):
    if '@' in login:
        query = {"email": login}
    else:
        query = {"username": login}
    user = User.query.filter_by(**query).one_or_none()
    if user and user.check_password(password):
        return user


def generate_confirmation_token(app, email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def send_confirmation_email(app, user, url, template, header):
    from ..celery import send_email_async
    token = generate_confirmation_token(app, user.email)
    confirm_url = url_for(url, token=token, _external=True)
    html = render_template(template, subject=header, confirm_url=confirm_url, user=user)
    email_data = {
        'subject': header,
        'html': html,
        'recipients': [user.email],
        'sender': app.config['MAIL_DEFAULT_SENDER']
    }
    send_email_async.delay(**email_data)


def do_register_user(username, email, password):
    user = User(username.strip(), email.strip(), password, False)
    user.profile = UserProfile()
    db.session.add(user)
    db.session.commit()
    wm.emit_signal(SIG_NEW_USER, request.path, msg=f'New user *{username}* has been registered')


def init_app(app):
    csrf = CSRFProtect(app)  # pylint: disable=W0612
    login_manager = LoginManager(app)
    mail = Mail(app)
    app.mail = mail
    auth = Blueprint('auth', __name__, template_folder='templates')

    @login_manager.user_loader
    def load_user(user_id):   # pylint: disable=W0613,W0612
        return User.query.get(user_id)

    @login_manager.header_loader
    def load_user_from_header(header_val):   # pylint: disable=W0613,W0612
        if header_val.startswith('Bearer'):
            header_val = header_val.replace('Bearer ', '', 1)
            try:
                data = decode_token(app.config['SECRET_KEY'], header_val, app.config['BEARER_TOKEN_EXPIRATION'])
                user = User.query.filter_by(id=data['user_id'], username=data['username'], email=data['email']).one_or_none()
                if user and user.active:
                    return user
            except (BadSignature, BadTimeSignature, KeyError):
                pass

    @auth.route('/login', methods=['POST'])
    def login():  # pylint: disable=W0613,W0612
        form = LoginForm()
        if form.validate():
            user = authenticate(form.login.data, form.password.data)
            if user and user.active:
                login_user(user)
                if not os.path.isfile(current_app.config['MAINTENANCE_FILE']):
                    LoginHistory.add_record(user.username, request)
                schema = UserSchema()
                return jsonify(schema.dump(user))
            elif not user:
                abort(401, 'Invalid username or password')
            elif not user.active:
                abort(401, 'Account is not active, please contact administrators')
        return jsonify(form.errors), 401

    @auth.route('/change_password', methods=['POST'])
    @auth_required
    def change_password():  # pylint: disable=W0613,W0612
        form = UserChangePasswordForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.old_password.data):
                form.errors['old_password'] = ['The old password is incorrect']
                return jsonify(form.errors), 400
            current_user.assign_password(form.password.data)
            db.session.add(current_user)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify(form.errors), 400

    @auth.route('/user_profile_by_name/<string:username>', methods=['GET'])
    @auth_required(permissions=['admin'])
    def get_user_profile_by_username(username):
        user = User.query.filter(User.username == username).first_or_404()
        data = UserSchema().dumps(user)
        return data, 200

    @auth.route('/delete_account', methods=['DELETE'])
    @auth_required
    def delete_account():  # pylint: disable=W0613,W0612
        """ Delete user account.
         User and all its references are permanently removed from db and disk.
         """
        from ..models.db_models import Account
        from ..celery import send_email_async

        username = current_user.username
        recipient = current_app.config['MAIL_DEFAULT_SENDER']
        account = Account.query.filter_by(type="user", owner_id=current_user.id).first()
        db.session.delete(account)
        db.session.commit()
        db.session.delete(current_user)
        db.session.commit()

        # send email into admin
        # TODO: this is just notification for mergin admin, we might want to do something better for statistics
        # TODO: also it might be cleaner to do it outside of auth module, e.g. on delete signal
        email_data = {
            'subject': f'{username} has been deleted',
            'html': f'user {username} has deleted their account',
            'recipients': [recipient],
            'sender': current_app.config['MAIL_DEFAULT_SENDER']
        }
        send_email_async.delay(**email_data)

        wm.emit_signal(SIG_DELETED_USER, request.path, msg=f'User *{username}* has been deleted')
        return jsonify({"success": True})

    @auth.route('/logout')
    @auth_required
    def logout():  # pylint: disable=W0613,W0612
        logout_user()
        return jsonify({"success": True})

    @auth.route('/resend_confirm_email')
    @auth_required
    def resend_confirm_email():  # pylint: disable=W0613,W0612
        send_confirmation_email(
            app,
            current_user,
            'auth.confirm_email',
            'email/email_confirmation.html',
            'Email confirmation'
        )
        return jsonify({"success": True})

    def confirm_token(token, expiration=3600*24*3):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt=app.config['SECURITY_PASSWORD_SALT'],
                max_age=expiration
            )
        except:
            return
        return email

    @auth.route('/user', methods=['POST'])
    @auth_required(permissions=['admin'])
    def register_user():  # pylint: disable=W0613,W0612
        form = RegisterUserForm()
        if form.validate():
            do_register_user(form.username.data, form.email.data, '')
            return jsonify({"success": True}), 200
        return jsonify(form.errors), 400

    @auth.route('/confirm/<token>', methods=['GET'])
    def confirm_email(token):  # pylint: disable=W0613,W0612
        from ..celery import send_email_async

        email = confirm_token(token)
        if not email:
            abort(400, "Invalid token")

        user = User.query.filter_by(email=email).first_or_404()
        if user.verified_email:
            return render_template('email_verified.html')

        if not user.check_password(''):
            user.verified_email = True
            db.session.add(user)
            db.session.commit()
            # send welcome email if user is freshly registered
            if user.profile.registration_date and user.profile.registration_date > datetime.utcnow() - timedelta(hours=1):
                html = render_template('email/welcome_email.html', subject="Welcome to Mergin!")
                email_data = {
                    'subject': "Welcome to Mergin",
                    'html': html,
                    'recipients': [user.email],
                    'sender': app.config['MAIL_DEFAULT_SENDER']
                }
                send_email_async.delay(**email_data)

        return render_template('email_verified.html')

    @auth.route('/password_changed', methods=['GET'])
    def password_changed():  # pylint: disable=W0613,W0612
        return render_template('password_reset_complete.html')  # pragma: no cover

    @auth.route('/confirm_password/<token>', methods=['GET', 'POST'])
    def confirm_new_password(token):  # pylint: disable=W0613,W0612
        email = confirm_token(token)
        if not email:
            abort(400, "Invalid token")

        user = User.query.filter_by(email=email).first_or_404()
        # user should confirm email first
        if not user.active:
            abort(400, "Account is not active")

        form = UserPasswordForm(request.form)
        if request.method == 'POST':
            form = UserPasswordForm()
            if form.validate():
                user.assign_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('auth.password_changed'))

        return render_template('change_password_form.html', form=form)

    @auth.route('/password_reset', methods=['POST'])
    def password_reset():  # pylint: disable=W0613,W0612
        form = ResetPasswordForm()
        if not form.validate():
            return jsonify(form.errors), 404

        user = User.query.filter(func.lower(User.email) == func.lower(form.email.data.strip())).one_or_none()
        if not user:
            return jsonify({"email": ["Account with given email does not exists"]}), 404
        if not user.active:
            # user should confirm email first
            return jsonify({"email": ["Account is not active"]}), 400

        send_confirmation_email(
            app,
            user,
            '.confirm_new_password',
            'email/password_reset.html',
            'Password reset'
        )
        return jsonify({"success": True})

    if app.config['USER_SELF_REGISTRATION']:
        @auth.route('/signup', methods=['POST'])
        def self_register_user():  # pylint: disable=W0613,W0612
            form = UserRegistrationForm()
            if form.validate_on_submit():
                do_register_user(form.username.data, form.email.data, form.password.data)
                user = User.query.filter(User.username == form.username.data).first()
                send_confirmation_email(
                    app,
                    user,
                    'auth.confirm_email',
                    'email/user_registration.html',
                    'Email confirmation'
                )
                login_user(user)
                LoginHistory.add_record(user.username, request)
                schema = UserSchema()
                return jsonify(schema.dump(user))
            return jsonify(form.errors), 400

    @auth.route('/user/<string:username>', methods=['DELETE'])
    @auth_required(permissions=['admin'])
    def delete_user(username):  # pylint: disable=W0613,W0612
        from ..models.db_models import Account

        user = User.query.filter_by(username=username).first_or_404("User not found")
        account = Account.query.filter_by(type="user", owner_id=user.id).first()
        db.session.delete(account)
        db.session.commit()
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})

    @auth.route('/user/profile', methods=['POST'])
    @auth_required
    def update_user_profile():  # pylint: disable=W0613,W0612
        form = UserProfileDataForm.from_json(request.json)
        email_changed = current_user.email != form.email.data.strip()
        if not form.validate_on_submit():
            return jsonify(form.errors), 400
        if email_changed:
            user = User.query.filter(func.lower(User.email) == func.lower(form.email.data.strip())).first()
            if user:
                form.email.errors.append("Email already exists")
                return jsonify(form.errors), 400
            current_user.verified_email = False

        form.update_obj(current_user.profile)
        form.update_obj(current_user)
        db.session.add(current_user)
        db.session.commit()
        if email_changed:
            resend_confirm_email()

        return jsonify({"success": True})

    @auth.route('/user/<string:username>', methods=['POST'])
    @auth_required(permissions=['admin'])
    def update_user(username):  # pylint: disable=W0613,W0612
        form = UserForm.from_json(request.json)
        if not form.validate_on_submit():
            return jsonify(form.errors), 400

        user = User.query.filter_by(username=username).first_or_404("User not found")
        form.update_obj(user)
        db.session.add(user)
        db.session.commit()
        return jsonify(UserSchema().dump(user))

    @auth.route('/user/search', methods=['GET'])
    @auth_required
    def search_users():  # pylint: disable=W0613,W0612
        """
        search by like param returns results in order: 1.) match is on start of words - ordered by id
                                                       2.) match is anywhere - ordered by id
        """
        query = None
        ids = request.args.get('id')
        names = request.args.get('names')
        like = request.args.get('like')
        users = User.query.filter_by(active=True)
        schema = UserSearchSchema(many=True)
        if ids:
            ids = request.args.get('id')
            try:
                ids = map(int, ids.split(','))
                query = User.id.in_(ids)
            except (ValueError, AttributeError):
                pass
        elif names:
            names = names.split(",")
            query = User.username.in_(names)
        elif like:
            ilike = "{}%".format(like)
            # match on start of words
            query_username_prioritized = User.username.ilike(ilike) | User.username.op("~")(f'[\\.|\\-|_| ]{like}.*')
            users1 = users.filter(query_username_prioritized).order_by(User.username).limit(10).all()
            if len(users1) < 10:
                # match anywhere except the previous results
                query_match_anywhere = User.username.ilike(f"%{ilike}") & User.id.notin_([usr.id for usr in users1])
                users2 = users.filter(query_match_anywhere).order_by(User.username).limit(10 - len(users1)).all()
                users1.extend(users2)
            return jsonify(schema.dump(users1))
        if query is not None:
            users = users.filter(query).order_by(User.username)

        return jsonify(schema.dump(users.limit(10).all()))

    app.register_blueprint(auth, url_prefix='/auth')
