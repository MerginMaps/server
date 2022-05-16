# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

from flask import jsonify, abort

from ..auth import auth_required
from ..auth.models import User
from ..models.db_models import Namespace, Account
from ..models.schemas import NamespaceSchema
from ..organisation.models import Organisation


def check_access_to_namespace(namespace, user):
    Namespace.query.filter_by(name=namespace).first_or_404()
    org = Organisation.query.filter_by(name=namespace).first()
    if user.username != namespace and not (org and user.id in org.writers):
        abort(403, "Permission denied.")


@auth_required
def search_namespace(namespace_type, q=None):  # pylint: disable=W0613,W0612
    """ Search namespace by query """
    namespaces = []
    if namespace_type == "user":
        namespaces = Namespace.query.join(Namespace.account).join(User, User.username == Namespace.name).filter(User.active, Account.type == "user", Namespace.name.ilike(f"{q}%")).limit(5).all() if q else []
    elif namespace_type == "organisation":
        namespaces = Namespace.query.join(Namespace.account).join(Organisation, Organisation.name == Namespace.name).filter(Organisation.active, Account.type == "organisation", Namespace.name.ilike(f"{q}%")).limit(5).all() if q else []
    data = NamespaceSchema(many=True).dump(namespaces)
    return jsonify(data)
