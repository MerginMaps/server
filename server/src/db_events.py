# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import os
from flask import render_template, current_app, abort
from sqlalchemy import event

from . import db
from .auth.models import User, UserProfile
from .models.db_models import Namespace, Project, ProjectAccess, Account, RemovedProject
from .organisation import Organisation, OrganisationInvitation
from .celery import send_email_async
from .storages.disk import move_to_tmp


def before_namespace_delete(mapper, connection, namespace):  # pylint: disable=W0612
    """ Remove namespace projects including project files on disk. Also remove project backups for restore """
    projects = Project.query.filter_by(namespace=namespace.name).all()
    for project in projects:
        if os.path.exists(project.storage.project_dir):
            project.storage.delete()

    removed_projects = RemovedProject.query.filter_by(namespace=namespace.name).all()
    rp_table = RemovedProject.__table__
    for rp in removed_projects:
        rp_dir = os.path.abspath(os.path.join(current_app.config['LOCAL_PROJECTS'], rp.properties["storage_params"]["location"]))
        if os.path.exists(rp_dir):
            move_to_tmp(rp_dir)
        connection.execute(removed_projects.delete().where(rp_table.c.id == rp.id))


def add_user_namespace(mapper, connection, user):  # pylint: disable=W0612
    ns = Namespace.query.filter_by(name=user.username).first()
    if ns:
        abort(400, "Namespace already exists")
    account_table = Account.__table__
    connection.execute(account_table.insert().values(owner_id=user.id, type="user"))
    account = Account.query.filter_by(type='user', owner_id=user.id).first()
    ns_table = Namespace.__table__
    connection.execute(ns_table.insert().values(name=user.username, account_id=account.id))
    # emit signal that account has been created
    account.created(connection)


def remove_user_references(mapper, connection, user):  # pylint: disable=W0612
    q = Project.access.has(ProjectAccess.owners.contains([user.id])) \
        | Project.access.has(ProjectAccess.readers.contains([user.id])) \
        | Project.access.has(ProjectAccess.readers.contains([user.id]))
    projects = Project.query.filter(q).all()

    def filter_user(ids):
        return filter(lambda i: i != user.id, ids)

    if projects:
        pa_table = ProjectAccess.__table__
        for p in projects:
            pa = p.access
            connection.execute(
                pa_table.update().where(pa_table.c.project_id == p.id),
                owners=filter_user(pa.owners),
                writers=filter_user(pa.writers),
                readers=filter_user(pa.readers)
            )

    # remove pending invitations for user
    inv_table = OrganisationInvitation.__table__
    connection.execute(inv_table.delete().where(inv_table.c.username == user.username))

    # remove from organisations
    q = Organisation.owners.contains([user.id]) \
        | Organisation.readers.contains([user.id]) \
        | Organisation.admins.contains([user.id]) \
        | Organisation.writers.contains([user.id])
    organisations = Organisation.query.filter(q).all()

    if organisations:
        o_table = Organisation.__table__
        for o in organisations:
            # in case of user is the only owner, remove also whole organisation
            if o.owners == [user.id]:
                connection.execute(inv_table.delete().where(inv_table.c.org_name == o.name))
                connection.execute(o_table.delete().where(o_table.c.name == o.name))

            connection.execute(
                o_table.update().where(o_table.c.name == o.name),
                owners=filter_user(o.owners),
                writers=filter_user(o.writers),
                readers=filter_user(o.readers),
                admins=filter_user(o.admins)
            )


def project_post_delete_actions(mapper, connection, project):  # pylint: disable=W0612
    """
    After project is deleted inform users by sending email.

    :param project: Project object
    """
    if not project.access:
        return

    users_ids = list(set(project.access.owners + project.access.writers + project.access.readers))
    users_profiles = UserProfile.query.filter(UserProfile.user_id.in_(users_ids)).all()
    for profile in users_profiles:
        if not (profile.receive_notifications and profile.user.verified_email):
            continue

        email_data = {
            'subject': f'Mergin project {"/".join([project.namespace, project.name])} has been deleted',
            'html': render_template('email/removed_project.html', subject="Project deleted", project=project, username=profile.user.username),
            'recipients': [profile.user.email],
            'sender': current_app.config['MAIL_DEFAULT_SENDER']
        }
        send_email_async.delay(**email_data)


def check(session):
    if os.path.isfile(current_app.config['MAINTENANCE_FILE']):
        abort(503, "Service unavailable due to maintenance, please try later")


def before_user_profile_updated(mapper, connection, target):
    """
    Before profile updated, inform user by sending email about that profile that changed
    Just send email if user want to receive notifications
    """
    if target.receive_notifications and target.user.verified_email:
        state = db.inspect(target)
        changes = {}

        for attr in state.attrs:
            hist = attr.load_history()
            if not hist.has_changes():
                continue

            before = hist.deleted[0]
            after = hist.added[0]
            field = attr.key

            # if boolean, show Yes or No
            if before is not None and isinstance(before, bool):
                before = 'Yes' if before is True else 'No'
            if after is not None and isinstance(after, bool):
                after = 'Yes' if after is True else 'No'

            profile_key = field.title().replace('_', ' ')
            changes[profile_key] = {
                'before': before,
                'after': after
            }

        # inform user
        if changes:
            email_data = {
                'subject': 'Profile has been changed',
                'html': render_template('email/profile_changed.html', subject="Profile update", user=target.user, changes=changes),
                'recipients': [target.user.email],
                'sender': current_app.config['MAIL_DEFAULT_SENDER']
            }
            send_email_async.delay(**email_data)


def add_org_namespace(mapper, connection, organisation):  # pylint: disable=W0612
    ns = Namespace.query.filter_by(name=organisation.name).first()
    if ns:
        abort(400, "Namespace already exists")
    account_table = Account.__table__
    connection.execute(account_table.insert().values(owner_id=organisation.id, type="organisation"))
    account = Account.query.filter_by(type='organisation', owner_id=organisation.id).first()
    ns_table = Namespace.__table__
    connection.execute(ns_table.insert().values(name=organisation.name, account_id=account.id))
    account.created(connection)


def register_events():
    event.listen(User, "after_insert", add_user_namespace)
    event.listen(User, "before_delete", remove_user_references)
    event.listen(Project, "after_delete", project_post_delete_actions)
    event.listen(db.session, 'before_commit', check)
    event.listen(UserProfile, 'after_update', before_user_profile_updated)
    event.listen(Namespace, "before_delete", before_namespace_delete)
    event.listen(Organisation, "after_insert", add_org_namespace)


def remove_events():
    event.remove(User, "after_insert", add_user_namespace)
    event.remove(User, "before_delete", remove_user_references)
    event.remove(Project, "after_delete", project_post_delete_actions)
    event.remove(db.session, 'before_commit', check)
    event.remove(UserProfile, 'after_update', before_user_profile_updated)
    event.remove(Namespace, "before_delete", before_namespace_delete)
    event.remove(Organisation, "after_insert", add_org_namespace)
