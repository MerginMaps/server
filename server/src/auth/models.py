# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import datetime
import bcrypt
from .. import db
from ..mergin_utils import get_user_agent, get_ip


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, info={'label': 'Username'})
    email = db.Column(db.String(120), unique=True)

    passwd = db.Column(db.String(80), info={'label': 'Password'}) #salted + hashed

    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean)
    verified_email = db.Column(db.Boolean, default=False)
    inactive_since = db.Column(db.DateTime(), nullable=True, index=True)

    def __init__(self, username, email, passwd, is_admin=False):

        self.username = username
        self.email = email
        self.assign_password(passwd)
        self.is_admin = is_admin

    def __repr__(self):
        return '<User %r>' % self.username

    def check_password(self, password):
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.checkpw(password, self.passwd.encode('utf-8'))

    def assign_password(self, password):
        if isinstance(password, str):
            password = password.encode('utf-8')
        self.passwd = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

    @property
    def is_authenticated(self):
        """ For Flask-Login """
        return True

    @property
    def is_active(self):
        """ For Flask-Login """
        return self.active

    @property
    def is_anonymous(self):
        """ For Flask-Login """
        return False

    def get_id(self):
        """ For Flask-Login ... must return unicode user ID"""
        return str(self.id)


class UserProfile(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    receive_notifications = db.Column(db.Boolean, default=True, index=True)
    first_name = db.Column(db.String(256), nullable=True, info={'label': 'First name'})
    last_name = db.Column(db.String(256), nullable=True, info={'label': 'Last name'})
    registration_date = db.Column(db.DateTime(), nullable=True, info={'label': 'Date of creation of user account'}, default=datetime.datetime.utcnow)

    user = db.relationship("User",
                           uselist=False,
                           backref=db.backref("profile", single_parent=True, uselist=False, cascade="all,delete"))


class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.datetime.utcnow, index=True)
    username = db.Column(db.String, index=True)
    user_agent = db.Column(db.String, index=True)
    ip_address = db.Column(db.String, index=True)
    ip_geolocation_country = db.Column(db.String, index=True)

    def __init__(self, username, ua, ip):
        self.username = username
        self.user_agent = ua
        self.ip_address = ip

    @staticmethod
    def add_record(username, request):
        ua = get_user_agent(request)
        ip = get_ip(request)
        # ignore login attempts coming from urllib - related to db sync tool
        if "DB-sync" in ua:
            return
        lh = LoginHistory(username, ua, ip)
        db.session.add(lh)
        db.session.commit()

