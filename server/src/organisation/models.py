# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, ENUM
from .. import db, current_app


class Organisation(db.Model):
    """ Organization db class.

    Organisation is one-to-one with Mergin namespace (which is unique).

    Organization supports tiers, with default 'free' which means organisation is not ready to use.

    Organization access is managed by access list control:
    Owners: users who are allowed remove organisation or change billing
    Admins: users who can administer users for organisation (except owners)
    Writers: writers have read-write access to organisation namespace
    Readers: reader have read-only access to organisation namespace

    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # modified only by owners
    name = db.Column(db.String, nullable=False, index=True)
    description = db.Column(db.String, nullable=True)
    owners = db.Column(ARRAY(db.Integer), server_default="{}")
    # access modified also by admins
    admins = db.Column(ARRAY(db.Integer), server_default="{}")
    writers = db.Column(ARRAY(db.Integer), server_default="{}")
    readers = db.Column(ARRAY(db.Integer), server_default="{}")
    registration_date = db.Column(db.DateTime(), nullable=True, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    inactive_since = db.Column(db.DateTime(), nullable=True, index=True)

    __table_args__ = (db.UniqueConstraint('name'),
                      db.Index('ix_org_owners', owners, postgresql_using="gin"),
                      db.Index('ix_org_readers', readers, postgresql_using="gin"),
                      db.Index('ix_org_writers', writers, postgresql_using="gin"),
                      db.Index('ix_org_admins', admins, postgresql_using="gin"),)

    def __init__(self, creator_id, name, **kwargs):
        self.name = name
        self.owners = [creator_id]
        self.admins = [creator_id]
        self.writers = [creator_id]
        self.readers = [creator_id]
        self.description = kwargs.get('description', None)
        self.active = True

    @staticmethod
    def find_by_member_id(user_id):
        return Organisation.query.filter(
            or_(
                Organisation.owners.contains([user_id]),
                Organisation.admins.contains([user_id]),
                Organisation.writers.contains([user_id]),
                Organisation.readers.contains([user_id])
            )
        ).filter_by(active=True).all()

    def get_member_role(self, user_id):
        for role in ('owners', 'admins', 'writers', 'readers'):
            if user_id not in getattr(self, role):
                continue
            return role.rstrip('s')


class OrganisationInvitation(db.Model):
    """ Organization Invitations db class.

    Adding new users to Organization is invitation based with required confirmation.
    """
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String, db.ForeignKey("organisation.name", ondelete="CASCADE"))
    username = db.Column(db.String, db.ForeignKey("user.username", ondelete="CASCADE"))
    role = db.Column(ENUM('reader', 'writer', 'admin', 'owner', name='role'), nullable=False)
    expire = db.Column(db.DateTime)

    organisation = db.relationship(
        "Organisation",
        uselist=False,
        backref=db.backref("invitations", single_parent=True, uselist=False, cascade="all,delete")
    )

    user = db.relationship("User", uselist=False)

    def __init__(self, org_name, username, role):
        self.org_name = org_name
        self.username = username
        self.role = role
        self.expire = datetime.utcnow() + timedelta(seconds=current_app.config['ORGANISATION_INVITATION_EXPIRATION'])

    def accept(self):
        """ The invitation accepted
        """
        attribute = self.role + 's'
        roles = getattr(self.organisation, attribute)
        roles.append(self.user.id)
        db.session.refresh(self.organisation)
        setattr(self.organisation, attribute, roles)
        db.session.add(self.organisation)
        db.session.delete(self)
        db.session.commit()

    def is_expired(self):
        """ Check if invitation is expired
        :rtype: bool
        """
        return datetime.utcnow() > self.expire
