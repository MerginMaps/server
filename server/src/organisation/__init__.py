# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from flask import Blueprint, jsonify, request, abort, render_template, current_app
from flask_login import current_user
from sqlalchemy import or_, func

from ..auth import auth_required
from ..auth.models import User
from .forms import UpdateOrganisationForm, AccessForm, CreateOrganisationForm, OwnerAccessForm, OrganisationInvitationForm
from .models import Organisation, OrganisationInvitation
from ..models.db_models import Namespace, Account
from .schemas import OrganisationSchema, OrganisationInvitationSchema
from .. import db, wm, SIG_NEW_ORGANISATION, SIG_DELETED_ORGANISATION


def find_organisations_by_username(username):
    user = User.query.filter_by(username=username).first_or_404()

    organisations = Organisation.query.filter(
        or_(
            Organisation.owners.contains([user.id]),
            Organisation.admins.contains([user.id]),
            Organisation.writers.contains([user.id]),
            Organisation.readers.contains([user.id])
        )
    ).filter_by(active=True).all()

    return organisations


def init_app(app):
    organisation = Blueprint("organisation", __name__, template_folder='templates')

    def get_org_by_name(name, only_active=True):
        query = Organisation.query.filter_by(name=name)
        if only_active:
            query = query.filter_by(active=True)
        return query.first_or_404(f"Organisation {name} not found")

    @organisation.route('/', methods=['GET'])
    @auth_required
    def get_organisations():  # noqa: E501
        """List mergin organisations a current user has (at least read) access to.

        :rtype: List[Organisation]
        """
        organisations = find_organisations_by_username(current_user.username)
        data = OrganisationSchema(many=True, context={'user': current_user}).dump(organisations)
        return jsonify(data), 200

    @organisation.route('/', methods=['POST'])
    @auth_required
    def create_organisation():  # noqa: E501
        """ Create a new organisation.
        :rtype: None
        """
        free_orgs = Organisation.query.join(Account, Account.owner_id == Organisation.id).join(Namespace, Namespace.account_id == Account.id)\
            .filter(Organisation.owners.contains([current_user.id]))\
            .filter((Namespace.storage == 0))\
            .filter(Organisation.active)\
            .count()
        if free_orgs > 2:
            abort(400, "Too many free organisations")

        form = CreateOrganisationForm.from_json(request.json)
        if not form.validate_on_submit():
            return jsonify(form.errors), 400

        name = form.name.data
        ns = Namespace.query.filter(func.lower(Organisation.name) == func.lower(name)).first()
        if ns:
            abort(409, f"Namespace {name} already exist, please choose another name.")

        org = Organisation(creator_id=current_user.id, **form.data)
        db.session.add(org)
        db.session.commit()
        wm.emit_signal(SIG_NEW_ORGANISATION, request.path, msg=f'New organisation *{name}* has been created')
        return jsonify({"success": True}), 201

    @organisation.route('/<name>', methods=['GET'])
    @auth_required
    def get_organisation_by_name(name):  # noqa: E501
        """ Return organisation by name.

        :param name: name of organisation
        :type name: str
        :rtype: Organisation
        """
        org = get_org_by_name(name, only_active=not current_user.is_admin)
        if current_user.id not in org.readers and not current_user.is_admin:
            abort(403, "You do not have permissions to get organisation")
        data = OrganisationSchema(context={'user': current_user}).dump(org)
        return data, 200

    @organisation.route('/<name>', methods=['PATCH'])
    @auth_required
    def update_organisation(name):  # noqa: E501
        """ Update organisation.

        Information fields (name, description) and owners to be updated only by organisation owners.

        :param name: name of organisation
        :type name: str
        :rtype: Organisation
        """
        org = get_org_by_name(name)
        if current_user.id not in org.owners and not current_user.is_admin:
            abort(403, "You do not have permissions to update organisation")

        form = UpdateOrganisationForm.from_json(request.json)
        if not form.validate_on_submit():
            return jsonify(form.errors), 400

        form.populate_obj(org)
        db.session.add(org)
        db.session.commit()
        data = OrganisationSchema(context={'user': current_user}).dump(org)
        return data, 200

    @organisation.route('/<name>/access', methods=['PATCH'])
    @auth_required
    def update_access(name):  # noqa: E501
        """ Update access fields of organisation.

        Access fields: admins, writers, readers to be amended by organisation admins.

        :param name: name of organisation
        :type name: str
        :rtype: Organisation
        """
        if not request.is_json:
            abort(400, "Payload format should be json")

        org = get_org_by_name(name)
        usernames = list(
            set(request.json['owners']) |
            set(request.json['admins']) |
            set(request.json['writers']) |
            set(request.json['readers'])
        )
        users = User.query.with_entities(User.username, User.id).filter(User.username.in_(usernames)).all()
        users_map = {u.username: u.id for u in users}
        access = {}
        for key in ('owners', 'admins', 'writers', 'readers'):
            access[key] = []
            for username in request.json[key]:
                if username not in users_map:
                    continue
                access[key].append(users_map[username])

        if current_user.id in org.owners or current_user.is_admin:
            form = OwnerAccessForm().from_json(access)
        elif current_user.id in org.admins:
            form = AccessForm().from_json(access)
        else:
            abort(403, "You do not have permissions to update organisation members")

        if not form.validate_on_submit():
            return jsonify(form.errors), 400

        form.populate_obj(org)
        db.session.add(org)
        db.session.commit()
        data = OrganisationSchema(context={"user": current_user}).dump(org)
        return data, 200

    @organisation.route('/<name>', methods=['DELETE'])
    @auth_required
    def delete_organisation(name):  # noqa: E501
        """ Delete organisation.

        :param name: name of organisation
        :type name: str
        :rtype: None
        """
        org = Organisation.query.filter_by(name=name).first_or_404()
        if not current_user.is_admin and current_user.id not in org.owners:
            abort(403, "You do not have permissions to delete organisation")

        account = Account.query.filter_by(type='organisation', owner_id=org.id).first()
        db.session.delete(account)
        db.session.commit()
        db.session.delete(org)  # make sure to delete namespace and all projects
        db.session.commit()
        wm.emit_signal(SIG_DELETED_ORGANISATION, request.path, msg=f'Organisation *{name}* has been deleted')
        return jsonify({"success": True}), 200

    @organisation.route('/invitation/create', methods=['POST'])
    @auth_required
    def create_invitation():  # noqa: E501
        """ Create invitation to organisation.
        """
        from ..celery import send_email_async

        if not request.is_json:
            abort(400, "Payload format should be json")

        form = OrganisationInvitationForm.from_json(request.json)
        if not form.validate_on_submit():
            return jsonify(form.errors), 400

        username = form.data.get('username')
        org_name = form.data.get('org_name')
        invitation = OrganisationInvitation.query.filter_by(username=username, org_name=org_name).first()
        if invitation:
            abort(409, "Invitation already exist.")

        user = User.query.filter_by(username=username).first_or_404(f"User {username} not found")
        organisation = get_org_by_name(org_name)
        if current_user.id not in organisation.admins and current_user.id not in organisation.owners:
            abort(403, "You do not have permissions to create an invitation.")

        invitation = OrganisationInvitation(org_name=org_name, username=username, role=form.data.get('role'))
        db.session.add(invitation)
        db.session.commit()
        body = render_template(
            'email/organisation_invitation.html',
            subject='Organisation invitation',
            username=username,
            invitation=invitation,
            link=f"{request.url_root.rstrip('/')}/users/{username}/organisations"
        )
        email_data = {
            'subject': 'Organisation invitation',
            'html': body,
            'recipients': [user.email],
            'sender': current_app.config['MAIL_DEFAULT_SENDER']
        }
        send_email_async.delay(**email_data)
        return jsonify(OrganisationInvitationSchema().dump(invitation)), 201

    @organisation.route('/invitations/<type>/<name>', methods=['GET'])
    @auth_required
    def get_invitations(type, name):  # noqa: E501
        """ Get invitations of user.
        :param name: username or organisation name
        :type name: str
        :param type: type of subject user or org
        :type type: enumerate
        """
        data = None
        if type == "user":
            if current_user.username != name and not current_user.is_admin:
                abort(403, "You do not have permissions to list invitations")
            data = OrganisationInvitationSchema(many=True).dump(OrganisationInvitation.query.filter_by(username=name).all())
            if not data:
                User.query.filter_by(username=name).first_or_404(f"User {name} not found")
        elif type == "org":
            organisation = get_org_by_name(name)
            if (current_user.id not in organisation.admins and current_user.id not in organisation.owners) and not current_user.is_admin:
                abort(403, "You do not have permissions to list invitations.")
            data = OrganisationInvitationSchema(many=True).dump(OrganisationInvitation.query.filter_by(org_name=name))
        else:
            abort(400, "Invalid account type")

        return jsonify(data), 200

    @organisation.route('/invitation/<id>', methods=['GET'])
    @auth_required
    def get_invitation(id):  # noqa: E501
        """ Get invitation detail.
        :param id: invitation id
        :type id: int
        """
        invitation = OrganisationInvitation.query.filter_by(id=id).first_or_404(f"Invitation {id} not found")
        if invitation.username != current_user.username and \
                current_user.id not in invitation.organisation.owners and \
                current_user.id not in invitation.organisation.admins:
            abort(403, "You do not have permissions to access invitation")

        data = OrganisationInvitationSchema().dump(invitation)
        return jsonify(data), 200

    @organisation.route('/invitation/confirm/<int:id>', methods=['POST'])
    @auth_required
    def accept_invitation(id):  # noqa: E501
        """ Accept invitation.
        :param id: invitation id
        :type id: int
        """
        invitation = OrganisationInvitation.query.get_or_404(id, "Invitation does not exist")
        if invitation.username != current_user.username:
            abort(403, "You do not have permissions to accept invitation")
        if invitation.is_expired():
            abort(400, "This invitation is already expired.")

        invitation.accept()
        org = OrganisationSchema(context={"user": current_user}).dump(invitation.organisation)
        return jsonify(org), 200

    @organisation.route('/invitation/<int:id>', methods=['DELETE'])
    @auth_required
    def delete_invitation(id):  # noqa: E501
        """ Delete/reject organisation invitation.
        :param id: invitation id
        :type id: int
        """
        from ..celery import send_email_async

        invitation = OrganisationInvitation.query.get_or_404(id, "Invitation does not exist")
        if invitation.username != current_user.username and \
                current_user.id not in invitation.organisation.owners + invitation.organisation.admins:
            abort(403, "You do not have permissions to delete invitation")

        db.session.delete(invitation)
        db.session.commit()
        user = User.query.filter(User.username == invitation.username).first()

        body = render_template(
            'email/organisation_invitation_revoke.html',
            subject='Organisation invitation revoked',
            username=invitation.username,
            org_name=invitation.org_name
        )
        email_data = {
            'subject': 'Your organisation invitation has been revoked',
            'html': body,
            'recipients': [user.email],
            'sender': current_app.config['MAIL_DEFAULT_SENDER']
        }
        send_email_async.delay(**email_data)
        return '', 200

    app.register_blueprint(organisation, url_prefix='/orgs')
