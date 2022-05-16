# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.
import os
from pathlib import Path

from src.organisation.models import Organisation, OrganisationInvitation
from src.models.db_models import Namespace, ProjectTransfer, Project, ProjectVersion, Upload, ProjectAccess, Account
from src.auth.models import User, UserProfile
from src import db
from . import DEFAULT_USER, TEST_ORG
from .utils import add_user, create_project, cleanup


def test_remove_organisation(client, diff_project):
    """ Test fully set up organisation is successfully removed incl:
    - organisation project
    - pending transfer
    - pending invitation
    - namespace
    - associated files
    """
    org_project = 'test'
    cleanup(client, [os.path.join(TEST_ORG, org_project)])

    # set up
    user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    org = Organisation(name=TEST_ORG, creator_id=user.id)
    add_user('user', 'user')
    invitation = OrganisationInvitation(TEST_ORG, 'user', 'reader')
    db.session.add(org)
    db.session.add(invitation)
    db.session.commit()
    project = create_project(org_project, TEST_ORG, user)
    proj_dir = Path(project.storage.project_dir)
    ns = Namespace.query.filter_by(name=org.name).first()
    project_transfer = ProjectTransfer(diff_project, ns, user.id)
    db.session.add(project_transfer)

    # delete organisation and thus associated projects and other objects
    account = Account.query.filter_by(type='organisation', owner_id=org.id).first()
    db.session.delete(account)
    db.session.commit()
    db.session.delete(org)
    db.session.commit()
    assert not Organisation.query.filter_by(name=TEST_ORG).count()
    assert not Namespace.query.filter_by(name=TEST_ORG).count()
    assert not Project.query.filter_by(name=org_project, namespace=TEST_ORG).count()
    assert not OrganisationInvitation.query.filter_by(org_name=TEST_ORG).count()  # handled as backreference
    assert not ProjectTransfer.query.filter_by(to_ns_name=TEST_ORG).count()
    assert not proj_dir.exists()


def test_close_user_account(client, diff_project, test_organisation):
    """ Test fully set up and active user is successfully removed incl:
        - user profile
        - user project
        - pending transfer
        - pending invitation
        - namespace
        - associated files
        - membership in organisation
        - project access to foreign projects
    """
    user_project = 'user_proj'
    cleanup(client, [os.path.join('user', user_project)])
    # set up
    mergin_user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    user = add_user('user', 'user')
    user_id = user.id
    user_ns = Namespace.query.filter_by(name=user.username).first()
    # user invited to TEST_ORG
    invitation = OrganisationInvitation(test_organisation.name, 'user', 'reader')
    db.session.add(invitation)
    # user is member of another organisation
    test_org = TEST_ORG + '2'
    org = Organisation(name=test_org, creator_id=mergin_user.id)
    org.owners.append(user.id)
    db.session.add(org)
    # user has access to mergin user diff_project
    diff_project.access.writers.append(user.id)
    # user contributed to another user project so he is listed in projects history
    change = {'added': [], 'removed': [], 'renamed': [], 'updated': []}
    pv = ProjectVersion(diff_project, 'v11', user.username, change, diff_project.files, '127.0.0.1')
    db.session.add(pv)
    db.session.add(diff_project)
    # user has it's own project
    p = create_project(user_project, user_ns.name, user)
    # user requested transfer of his project to org
    org_ns = Namespace.query.filter_by(name=org.name).first()
    project_transfer_out = ProjectTransfer(p, org_ns, user.id)
    db.session.add(project_transfer_out)
    # create pending transfer to user's namespace
    project_transfer_in = ProjectTransfer(diff_project, user_ns, mergin_user.id)
    db.session.add(project_transfer_in)
    # create user's own organisation to be closed with his account (since he is the only owner)
    user_org = Organisation(name='user.org', creator_id=user.id)
    org.owners.append(user.id)
    db.session.add(user_org)
    db.session.commit()

    # now remove user
    account = Account.query.filter_by(type="user", owner_id=user.id).first()
    db.session.delete(account)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()
    assert not User.query.filter_by(username='user').count()
    assert not UserProfile.query.filter_by(user_id=user_id).count()  # handled as backreference
    assert not Namespace.query.filter_by(name='user').count()
    assert not Project.query.filter_by(name=user_project, namespace='user').count()
    assert not OrganisationInvitation.query.filter_by(username='user').count()
    assert not ProjectTransfer.query.filter_by(requested_by=user_id).count()
    assert not ProjectTransfer.query.filter_by(to_ns_name='user').count()
    assert user_id not in org.owners
    assert user_id not in diff_project.access.writers
    assert not Organisation.query.filter_by(name='user.org').count()
    # user remains referenced in existing project version he created (as read-only ref)
    assert diff_project.versions[0].author == 'user'


def test_remove_project(client, diff_project, test_organisation):
    """ Test active project is successfully removed incl:
        - pending transfer
        - pending upload
        - project access
        - project versions
        - associated files
    """
    # set up
    mergin_user = User.query.filter_by(username=DEFAULT_USER[0]).first()
    project_dir = Path(diff_project.storage.project_dir)
    project_name = diff_project.name
    ns = Namespace.query.filter_by(name=test_organisation.name).first()
    project_transfer = ProjectTransfer(diff_project, ns, mergin_user.id)
    changes = {'added': [], 'removed': [], 'renamed': [], 'updated': []}
    upload = Upload(diff_project, 10, changes, mergin_user.id)
    db.session.add(project_transfer)
    db.session.add(upload)
    db.session.commit()
    project_id = diff_project.id

    # remove project
    db.session.delete(diff_project)
    db.session.commit()
    assert not Project.query.filter_by(id=project_id).count()
    assert not Upload.query.filter_by(project_id=project_id).count()
    assert not ProjectVersion.query.filter_by(project_id=project_id).count()
    assert not ProjectAccess.query.filter_by(project_id=project_id).count()
    assert not ProjectTransfer.query.filter_by(project_id=project_id).count()
    # files need to be deleted manually
    assert project_dir.exists()
    cleanup(client, [project_dir])

