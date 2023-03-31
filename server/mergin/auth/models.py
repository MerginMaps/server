# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from __future__ import annotations
import datetime
from typing import List

import bcrypt
from .. import db
from ..sync.utils import get_user_agent, get_ip


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, info={"label": "Username"})
    email = db.Column(db.String(120), unique=True)

    passwd = db.Column(db.String(80), info={"label": "Password"})  # salted + hashed

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
        return "<User %r>" % self.username

    def check_password(self, password):
        if isinstance(password, str):
            password = password.encode("utf-8")
        return bcrypt.checkpw(password, self.passwd.encode("utf-8"))

    def assign_password(self, password):
        if isinstance(password, str):
            password = password.encode("utf-8")
        self.passwd = bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

    @property
    def is_authenticated(self):
        """For Flask-Login"""
        return True

    @property
    def is_active(self):
        """For Flask-Login"""
        return self.active

    @property
    def is_anonymous(self):
        """For Flask-Login"""
        return False

    def get_id(self):
        """For Flask-Login ... must return unicode user ID"""
        return str(self.id)

    @staticmethod
    def search(like: str, limit: int = 10, only_active: bool = True) -> List[User]:
        """
        Find users using ilike pattern within username/email

        Results are returned in following order:
        1.) exact match - ordered by attribute
        2.) match is on start of the string - ordered by attribute
        3.) match is on start of words - ordered by attribute
        4.) match is anywhere - ordered by attribute
        """
        if only_active:
            users_query = User.query.filter_by(active=True)
        else:
            users_query = User.query
        attr = User.email if "@" in like else User.username
        # try with exact match
        users_found = (
            users_query.filter(attr.ilike(like)).order_by(attr).limit(limit).all()
        )
        # we keep searching until we have enough results
        if len(users_found) < limit:
            # prefix match except the previous results
            query_prefix = attr.ilike(f"{like}%") & User.id.notin_(
                [usr.id for usr in users_found]
            )
            users_prefix = (
                users_query.filter(query_prefix)
                .order_by(attr)
                .limit(limit - len(users_found))
                .all()
            )
            users_found.extend(users_prefix)
            if len(users_found) < limit:
                # match on start of words except the previous results
                query_prefix_words = attr.op("~")(
                    f"[\\.|\\-|_| ]{like}.*"
                ) & User.id.notin_([usr.id for usr in users_found])
                users_prefix_words = (
                    users_query.filter(query_prefix_words)
                    .order_by(attr)
                    .limit(limit - len(users_found))
                    .all()
                )
                users_found.extend(users_prefix_words)
                if len(users_found) < limit:
                    # match anywhere except the previous results
                    query_match_anywhere = attr.ilike(f"%{like}%") & User.id.notin_(
                        [usr.id for usr in users_found]
                    )
                    users_anywhere = (
                        users_query.filter(query_match_anywhere)
                        .order_by(attr)
                        .limit(limit - len(users_found))
                        .all()
                    )
                    users_found.extend(users_anywhere)
        return users_found


class UserProfile(db.Model):
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    receive_notifications = db.Column(db.Boolean, default=True, index=True)
    first_name = db.Column(db.String(256), nullable=True, info={"label": "First name"})
    last_name = db.Column(db.String(256), nullable=True, info={"label": "Last name"})
    registration_date = db.Column(
        db.DateTime(),
        nullable=True,
        info={"label": "Date of creation of user account"},
        default=datetime.datetime.utcnow,
    )

    user = db.relationship(
        "User",
        uselist=False,
        backref=db.backref(
            "profile", single_parent=True, uselist=False, cascade="all,delete"
        ),
    )

    def name(self):
        return f'{self.first_name if self.first_name else ""} {self.last_name if self.last_name else ""}'.strip()


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
