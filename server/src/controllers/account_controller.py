# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from datetime import datetime
from operator import and_

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user
from sqlalchemy import or_, desc, asc, true

from src.auth import AccountSearchSchema
from .. import db
from ..auth import auth_required
from ..models.db_models import Account, Namespace
from ..models.schemas import AccountSchema, AccountExtendedSchema
from ..auth.models import User
from ..models.db_models import Project, ProjectAccess, ProjectTransfer
from ..organisation.models import OrganisationInvitation, Organisation

account = Blueprint("account", __name__)


@account.route('/accounts/<int:account_id>', methods=['GET'])
@auth_required(permissions=['admin'])
def get_account_by_id(account_id):  # pylint: disable=W0613,W0612
    """ get account by id
    :rtype: Account
    """
    accounts = Account.query.get(account_id)
    data = AccountSchema().dump(accounts)
    return jsonify(data), 200


@account.route('/accounts/<path:type>', methods=['GET'])
@auth_required(permissions=['admin'])
def list_accounts(type):  # pylint: disable=W0613,W0612
    """ List of either user or organisation paginated accounts with optional filters and sort.

    :param type: account type, either 'user' or 'organisation'
    :type type: str
    :returns: Total number of accounts and paginated results for accounts
    :rtype: dict(total: int, accounts: List[Account])
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        abort(400, "Invalid query format")
    order_by = request.args.get('order_by')
    descending = str(request.args.get('descending', 'false')) == 'true'
    name = str(request.args.get('name', ''))
    if type == "user":
        model = User
        name_col = User.username
        active_col = User.active
    elif type == "organisation":
        model = Organisation
        name_col = Organisation.name
        active_col = Organisation.active
    else:
        abort(400, 'Invalid account type')

    query = db.session.query(
        Account.id,
        Account.type,
        name_col.label("name"),
        active_col.label("active"),
        Namespace.storage
    )\
        .join(model,  Account.owner_id == model.id) \
        .join(Namespace, Namespace.account_id == Account.id) \
        .filter(Account.type == type)

    if name:
        query = query.filter(name_col.ilike(f'%{name}%'))

    # sort by some column
    col = None
    if order_by:
        if order_by == 'name':
            col = name_col

    if col:
        query = query.order_by(desc(col)) if descending else query.order_by(asc(col))

    paginate = query.paginate(page, per_page, max_per_page=100)
    result = paginate.items
    total = paginate.total
    accounts = AccountExtendedSchema(many=True).dump(result)
    return jsonify(accounts=accounts, total=total), 200


@account.route('/change_account_status/<int:account_id>', methods=['PATCH'])
@auth_required(permissions=['admin'])
def change_account_status(account_id):
    """
    Change account active status to true or false

    :param account_id:
    :return changed status:
    """
    if request.json.get("status") is None:
        abort(400, "Status is empty")
    account = Account.query.get_or_404(account_id, "Account not found")
    owner = account.owner()
    owner.active = request.json.get("status")
    owner.inactive_since = datetime.utcnow() if not owner.active else None
    if request.json.get("status") is False:
        account.inactivated("deactivate")
    db.session.commit()

    return jsonify({'status': request.json.get("status")}), 200


@account.route('/account/<int:id>', methods=['DELETE'])
@auth_required
def close_account(id):  # pylint: disable=W0613,W0612
    """ Close account.
    All related objects remain (temporarily) in database and files on disk, following actions are done:

    - account holder is turned to inactive
    - users's reference from 3rd parties integration is removed (e.g. Stripe)
    - all references in projects' permissions are removed
    - all pending project transfers related to account namespace are removed
    - all membership in organisations and pending invitations are removed

    For permanent delete, account holder object needs to be deleted.
    """
    account = Account.query.get_or_404(id, f'Account {id} not found')
    if not account.can_edit(current_user.id) and not current_user.is_admin:
        abort(403)

    user = None
    organisation = None
    if account.type == 'user':
        user = User.query.get(account.owner_id)
        # remove membership in organisations
        organisations = Organisation.query.filter(or_(
            Organisation.owners.contains([user.id]),
            Organisation.admins.contains([user.id]),
            Organisation.writers.contains([user.id]),
            Organisation.readers.contains([user.id])
        )).all()

        user_organisation = next((o for o in organisations if o.owners == [user.id]), None)
        if user_organisation:
            abort(400, f"Can not close account because user is the only owner of organisation {user_organisation.name}")

        for org in organisations:
            for key in ('owners', 'admins', 'writers', 'readers'):
                value = set(getattr(org, key))
                if user.id in value:
                    value.remove(user.id)
                setattr(org, key, list(value))
            db.session.add(org)

        # remove user reference from shared projects
        shared_projects = Project.query \
            .filter(Project.namespace != account.namespace.name) \
            .filter(or_(
            Project.access.has(ProjectAccess.owners.contains([user.id])),
            Project.access.has(ProjectAccess.writers.contains([user.id])),
            Project.access.has(ProjectAccess.readers.contains([user.id]))
        )).all()

        for p in shared_projects:
            for key in ('owners', 'writers', 'readers'):
                value = set(getattr(p.access, key))
                if user.id in value:
                    value.remove(user.id)
                setattr(p.access, key, list(value))
            db.session.add(p)

        # remove pending invitations
        invitations = OrganisationInvitation.query.filter_by(username=user.username).all()
        for i in invitations:
            db.session.delete(i)

    else:
        organisation = Organisation.query.get(account.owner_id)
        invitations = OrganisationInvitation.query.filter_by(org_name=account.name()).all()
        for i in invitations:
            db.session.delete(i)

    # reset permissions for namespace's projects
    projects = Project.query.filter_by(namespace=account.namespace.name).all()
    for p in projects:
        p.access.owners = []
        p.access.writers = []
        p.access.readers = []
        db.session.add(p)

    # remove pending project transfers (both directions)
    transfers = ProjectTransfer.query.filter(or_(
        ProjectTransfer.from_ns_name == account.namespace.name,
        ProjectTransfer.to_ns_name == account.namespace.name
    )).all()
    for t in transfers:
        db.session.delete(t)

    account.inactivated("delete")

    # inactivate account
    owner = account.owner()
    owner.active = False
    owner.inactive_since = datetime.utcnow()

    db.session.add(account)
    db.session.commit()
    return '', 200

@account.route('/account/change_storage/<int:account_id>', methods=['POST'])
@auth_required(permissions=['admin'])
def change_storage(account_id):  # pylint: disable=W0613,W0612
    """ Change storage.
    Change account storage with new value
    - account_id account id
    - storage: new storage value in bytes
    """
    namespace = Namespace.query.filter(Namespace.account_id == account_id).first_or_404(f'Namespace for accountId: {account_id} not found')
    if not request.json.get("storage"):
        abort(400, "Storage is empty")
    try:
        storage = int(request.json.get("storage"))
    except Exception as e:
        abort(400, "Storage is not a number")
    namespace.storage = storage
    db.session.commit()
    return '', 200


@account.route('/accounts/search', methods=['GET'])
@auth_required(permissions=['admin'])
def search_accounts_by_name():  # pylint: disable=W0613,W0612
    """
    search by like param returns results in order: 1.) match is on start of words - ordered by id
                                                   2.) match is anywhere - ordered by id
    """
    from src.models.db_models import Account
    from src.organisation import Organisation

    query = db.session.query(
        Account.id,
        Account.type,
        Organisation.name,
        User.username
    ) \
        .outerjoin(Organisation, and_(Account.owner_id == Organisation.id, Account.type == "organisation")) \
        .outerjoin(User, and_(Account.owner_id == User.id, Account.type == "user")) \

    like = request.args.get('like')
    schema = AccountSearchSchema(many=True)
    if like:
        ilike = "{}%".format(like)
        accounts = query.filter(and_(User.active == true(), (User.username.ilike(ilike) | User.username.op("~")(f'[\\.|\\-|_| ]{like}.*'))) |
                                and_(Organisation.active == true(), Organisation.name.ilike(ilike))).limit(10).all()
    return jsonify(schema.dump(accounts))
