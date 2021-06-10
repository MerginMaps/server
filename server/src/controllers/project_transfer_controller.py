# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

from datetime import datetime, timedelta
from connexion import NoContent, request
from flask import abort, render_template, current_app
from flask_login import current_user
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.session import make_transient
from sqlalchemy import or_

from .. import db
from ..models.db_models import Project, ProjectTransfer, Namespace, Account, AccessRequest
from ..models.schemas import ProjectTransferSchema

from ..auth import auth_required
from ..auth.models import User
from ..permissions import require_project, ProjectPermissions, check_namespace_permissions
from .. import wm, SIG_PROJECT_TRANSFERED
from ..organisation.models import Organisation


@auth_required
def get_project_transfers(namespace):  # noqa: E501
    """List project transfers.

    :rtype: List[ProjectTransfer]
    """
    if not (check_namespace_permissions(namespace, current_user, 'admin') or current_user.is_admin):
        abort(403)
    transfers = ProjectTransfer.query.filter(or_(
        ProjectTransfer.to_ns_name == namespace,
        ProjectTransfer.from_ns_name == namespace)
    ).all()
    data = ProjectTransferSchema(many=True).dump(transfers)
    return data, 200


@auth_required
def request_transfer(namespace, project_name, data=None):
    """ Request transfer project.

    Request transfer project to another namespace.

    :param namespace: Namespace for project to look into.
    :type namespace: str
    :param project_name: Project name.
    :type project_name: str
    :param data: Request payload - destination namespace.
    :type data: dict | bytes
    :rtype: None
    """
    from ..celery import send_email_async

    project = require_project(namespace, project_name, ProjectPermissions.All)
    dest_ns = data.get('namespace', None)
    if not dest_ns:
        abort(400, "Missing destination namespace")
    to_ns = Namespace.query.filter_by(name=dest_ns).first_or_404(f"{dest_ns} namespace not found")
    pt = ProjectTransfer.query.filter_by(project_id=project.id, from_ns_name=project.namespace).first()
    if pt:
        abort(409, f"The project {project.namespace}/{project.name} is already in a transfer process")
    try:
        transfer = ProjectTransfer(project, to_ns, current_user.id)
        db.session.add(transfer)
        db.session.commit()

        if to_ns.account.type == "user":
            user = User.query.get(to_ns.account.owner_id)
            users = [user]
            link = f"{request.url_root.rstrip('/')}/users/{user.username}/projects"
        else:
            org = Organisation.query.get(to_ns.account.owner_id)
            users = User.query.filter(User.id.in_(org.admins)).all()
            link = f"{request.url_root.rstrip('/')}/organisations/{org.name}/projects"
        for user in users:
            body = render_template(
                'email/project_transfer_request.html',
                subject="Project transfer requested",
                username=user.username,
                project_name=project_name,
                namescape_to=dest_ns,
                namespace_from=namespace,
                link=link,
                expire=datetime.utcnow() + timedelta(seconds=current_app.config['TRANSFER_EXPIRATION'])
            )
            email_data = {
                'subject': 'Mergin project transfer request',
                'html': body,
                'recipients': [user.email],
                'sender': current_app.config['MAIL_DEFAULT_SENDER']
            }
            send_email_async.delay(**email_data)

        return NoContent, 201
    except ProjectTransfer.TransferError as e:
        abort(400, str(e))


@auth_required
def delete_transfer_project(id):
    """ Delete transfer project of Project Transfer data.

    Delete transfer project on the project transfer data

    :param id: project transfer id.
    :type id: str

    :rtype: None
    """
    project_transfer = ProjectTransfer.query.filter_by(id=id).first_or_404("Project transfer is not found")
    if not check_namespace_permissions(project_transfer.from_ns_name, current_user, 'admin') and not check_namespace_permissions(project_transfer.to_ns_name, current_user, 'admin'):
        abort(403, "You don't have access for transferring this project")
    db.session.delete(project_transfer)
    db.session.commit()
    return NoContent, 200


@auth_required
def execute_transfer_project(id, data=None):
    """ Execute transfer project of Project Transfer data.

    Only project namespace/name is modified. Files are saved on disk independently on project owner, hence not touched.

    :param id: project transfer id.
    :type id: str
    :param data: payload of post request
    :type data: dict
    :rtype: None
    """
    project_transfer = ProjectTransfer.query.filter_by(id=id).first_or_404("Project transfer not found")
    if not check_namespace_permissions(project_transfer.to_ns_name, current_user, 'admin'):
        abort(403, "You don't have access for transferring this project")

    # we check if user use new project name
    old_project_name = project_transfer.project.name
    old_project_id = project_transfer.project.id
    old_namespace = project_transfer.from_ns_name
    new_project_name = data.get('name', project_transfer.project.name)
    new_namespace = project_transfer.to_ns_name
    transfer_permission = data.get('transfer_permissions', True)

    # we validate if the project already exist in new namespace
    if Project.query.filter_by(name=new_project_name, namespace=project_transfer.to_ns.name).first():
        abort(409, f"Project {project_transfer.to_ns.name}/{new_project_name} already exists")

    # check if there is ongoing upload
    if project_transfer.project.uploads.first():
        abort(400, f"There is ongoing upload for {project_transfer.from_ns_name}/{project_transfer.project.name}. "
                   f"Please try later")

    # check if expired
    if project_transfer.is_expired():
        abort(400, "The request is already expired")

    # check if new owner has enough disk space to host new project
    new_ns = Namespace.query.filter_by(name=project_transfer.to_ns_name).first()
    if new_ns.disk_usage() + project_transfer.project.disk_usage > new_ns.storage:
        abort(400, "Disk quota reached")

    new_owner = new_ns.account.owner()
    if isinstance(new_owner, User):
        new_owner_id = new_owner.id
    elif isinstance(new_owner, Organisation):
        owner_user = User.query.filter_by(id=new_owner.owners[0]).first()
        if not owner_user:
            abort(400, "Target organisation does not have an owner to accept transfer")
        new_owner_id = owner_user.id
    else:
        assert False

    # all checks passed - let's transfer it
    # delete ongoing project access requests
    AccessRequest.query.filter(AccessRequest.namespace == old_namespace, AccessRequest.project_id == old_project_id).delete()
    db.session.commit()

    # change namespace/name
    project = project_transfer.project
    project.name = new_project_name
    project.namespace = project_transfer.to_ns.name

    # we change creator id to the new owner, either new user or first owner of organisation
    project.creator_id = new_owner_id

    # clean permissions if new owner decided for it or just append new owner
    if not transfer_permission:
        project.access.owners = [new_owner_id]
        project.access.readers = [new_owner_id]
        project.access.writers = [new_owner_id]
    else:
        if new_owner_id not in project.access.owners:
            project.access.owners.append(new_owner_id)
        if new_owner_id not in project.access.readers:
            project.access.readers.append(new_owner_id)
        if new_owner_id not in project.access.writers:
            project.access.writers.append(new_owner_id)

    db.session.add(project)
    flag_modified(project.access, "owners")
    flag_modified(project.access, "writers")
    flag_modified(project.access, "readers")
    db.session.commit()

    wm.emit_signal(
        SIG_PROJECT_TRANSFERED,
        request.path,
        msg=f'Project *{old_namespace}/{old_project_name}* has been transferred to *{new_namespace}/{new_project_name}*')
    return NoContent, 200
