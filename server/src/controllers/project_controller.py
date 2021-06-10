# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import json
import mimetypes
import os
import logging
import copy
from urllib.parse import quote
import uuid
from time import time
from datetime import datetime, timedelta
import psycopg2
from connexion import NoContent, request
from flask import abort, render_template, current_app, send_from_directory, jsonify, make_response
from pygeodiff import GeoDiffLibError
from sqlalchemy.orm import joinedload
from flask_login import current_user
from sqlalchemy.types import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import cast, and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from binaryornot.check import is_binary
from gevent import sleep

from .. import db, wm, SIG_NEW_PROJECT
from ..auth import auth_required
from ..auth.models import User, UserProfile
from ..models.db_models import Project, ProjectAccess, ProjectVersion, Namespace, Upload, RemovedProject
from ..models.schemas import ProjectSchema, ProjectListSchema, ProjectVersionSchema, FileInfoSchema, ProjectSchemaForVersion
from ..organisation.models import Organisation
from ..storages.storage import FileNotFound, DataSyncError, InitializationError
from ..storages.disk import save_to_file, move_to_tmp
from ..permissions import require_project, projects_query, ProjectPermissions, get_upload
from ..mergin_utils import generate_checksum, Toucher, int_version, is_file_name_blacklisted, get_ip, get_user_agent, \
    generate_location, is_valid_uuid
from ..util import is_name_allowed, mergin_secure_filename, get_path_from_files
from ..celery import send_email_async
from .namespace_controller import check_access_to_namespace


def _project_version_files(project, version=None):
    if version:
        pv = next((v for v in project.versions if v.name == version), None)
        if not pv:
            abort(404, "Project version does not exist")
        return pv.files
    return project.files


@auth_required
def add_project(namespace, project):  # noqa: E501
    """Add a new mergin project.

     # noqa: E501

    :param project: Project object that needs to be added to the database.
    :type project: dict | bytes

    :rtype: None
    """
    if not is_name_allowed(project['name']):
        abort(400, "Please use only alphanumeric or these -._~()'!*:@,; characters in project name.")

    project['name'] = project['name'].strip()
    if request.is_json:
        ua = get_user_agent(request)
        check_access_to_namespace(namespace, current_user)

        proj = Project.query.filter_by(name=project['name'], namespace=namespace).first()
        if proj:
            abort(409, "Project {} already exists!".format(project['name']))

        project['storage_params'] = {"type": "local", "location": generate_location()}

        p = Project(**project, creator=current_user, namespace=namespace)
        p.updated = datetime.utcnow()
        pa = ProjectAccess(p, public=project.get('public', False))

        template = project.get('template', None)
        ip = get_ip(request)
        if template:
            template = Project.query.\
                filter(Project.creator.has(username='TEMPLATES')).\
                filter(Project.name == template)\
                .first_or_404()
            # create mutable object
            temp_copy = copy.deepcopy(template)
            temp_files = ProjectSchema(only=('files',)).dump(temp_copy)
            changes = {"added": temp_files['files'], "renamed": [], "updated": [], "removed": []}
            version = ProjectVersion(p, 'v1', current_user.username, changes, template.files, ip, ua)
            p.latest_version = 'v1'
        else:
            changes = {"added": [], "renamed": [], "updated": [], "removed": []}
            version = ProjectVersion(p, 'v0', current_user.username, changes, [], ip, ua)
            p.latest_version = 'v0'
        try:
            p.storage.initialize(template_project=template)
        except Exception as exc:
            abort(400, f"Failed to initialize project: {str(exc)}")

        p.versions.append(version)
        db.session.add(p)
        db.session.add(pa)
        db.session.commit()

        wm.emit_signal(SIG_NEW_PROJECT, request.path, msg=f'New project *{namespace}/{project["name"]}* has been created')
        return NoContent, 200


@auth_required
def delete_project(namespace, project_name):  # noqa: E501
    """Delete a project.

     # noqa: E501

    :param project_name: name of project to delete.
    :type project_name: str

    :rtype: None
    """
    project = require_project(namespace, project_name, ProjectPermissions.Delete)
    rm_project = RemovedProject(project, current_user.username)
    db.session.add(rm_project)
    db.session.delete(project)
    db.session.commit()
    return NoContent, 200


def download_project(namespace, project_name, format=None, version=None):  # noqa: E501 # pylint: disable=W0622
    """Download dir for single project.

     # noqa: E501

    :param project_name: name of project to return.
    :type project_name: str
    :param format: output format
    :type format: str [zip]
    :param version: version tag name
    :type version: str

    :rtype: None
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    files = _project_version_files(project, version)
    try:
        return project.storage.download_files(files, format, version=version)
    except FileNotFound as e:
        abort(404, str(e))


def download_project_file(project_name, namespace, file, version=None, diff=None):  # noqa: E501
    """Download project file

    Download individual file or it's diff file from project. # noqa: E501

    :param project_name: Project name.
    :type project_name: str
    :param namespace: Namespace for project to look into.
    :type namespace: str
    :param file: Path to file.
    :type file: str
    :param version: Version tag.
    :type version: str
    :param diff: Ask for diff file instead of full one.
    :type diff: bool

    :rtype: None
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    files = _project_version_files(project, version)

    if diff and version:
        # get specific version of geodiff file modified in requested version
        file_obj = next((f for f in files if f['location'] == os.path.join(version, file)), None)
        if not file_obj:
            abort(404, file)
        if 'diff' not in file_obj:
            abort(404, f"No diff in particular file {file} version")
        file_path = file_obj['diff']['location']
    elif diff:
        abort(400, f"Changeset must be requested for particular file version")
    else:
        # get latest version of file
        file_path = next((f['location'] for f in files if f['path'] == file), None)

    if not file_path:
        abort(404, file)

    if version and not diff:
        project.storage.restore_versioned_file(file, version)

    if current_app.config['USE_X_ACCEL']:
        # encoding for nginx to be able to download file with non-ascii chars
        encoded_file_path = quote(file_path.encode("utf-8"))
        resp = make_response()
        resp.headers['X-Accel-Redirect'] = f"/download/{project.storage_params['location']}/{encoded_file_path}"
        resp.headers['X-Accel-Buffering'] = True
        resp.headers['X-Accel-Expires'] = 'off'
    else:
        resp = send_from_directory(project.storage.project_dir, file_path)
    abs_path = os.path.join(project.storage.project_dir, file_path)
    if not is_binary(abs_path):
        mime_type = "text/plain"
    else:
        mime_type = mimetypes.guess_type(abs_path)[0]
    resp.headers['Content-Type'] = mime_type
    resp.headers['Content-Disposition'] = 'attachment; filename={}'.format(quote(os.path.basename(file).encode("utf-8")))
    return resp


def get_project(project_name, namespace, since='', version=None):  # noqa: E501
    """Find project by name.

    Returns a single project with details about files including history for versioned files (diffs) if needed. # noqa: E501

    :param project_name: Name of project to return.
    :type project_name: str
    :param namespace: Namespace for project to look into.
    :type namespace: str
    :param since: Version to look up diff files history from.
    :type since: str
    :param version: Version to return files details for.
    :type version: str

    :rtype: ProjectDetail
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)

    if since and version:
        abort(400, "Parameters 'since' and 'version' are mutually exclusive")
    elif since:
        # append history for versioned files
        last_version = ProjectVersion.query.filter_by(project_id=project.id).order_by(
            ProjectVersion.created.desc()).first()
        for f in project.files:
            f['history'] = project.file_history(f['path'], since, last_version.name)
        data = ProjectSchema(exclude=['storage_params']).dump(project)
    elif version:
        # return project info at requested version
        version_obj = next((v for v in project.versions if v.name == version), None)
        if not version_obj:
            abort(404, "Project at requested version does not exist")
        data = ProjectSchemaForVersion().dump(version_obj)
    else:
        # return current project info
        data = ProjectSchema(exclude=['storage_params']).dump(project)
    return data, 200


def get_project_versions(namespace, project_name, version_id=None):  # noqa: E501
    """Get versions (history) of project.

    Returns a list of project versions with changes information. # noqa: E501

    :param project_name: Name of project to return versions for.
    :type project_name: str
    :param version_id:
    :type version_id: str

    :rtype: List[ProjectVersion]
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    query = ProjectVersion.query.filter(and_(ProjectVersion.project_id == project.id, ProjectVersion.name != "v0"))
    if version_id:
        query = ProjectVersion.query.filter_by(project_id=project.id).filter_by(name=version_id)
    versions = query.order_by(ProjectVersion.created.desc()).all()
    data = ProjectVersionSchema(exclude=['files'], many=True).dump(versions)
    return data, 200


def get_projects_by_names(data):  # noqa: E501
    """List mergin projects by list of  projects namespace and name.
    Returns limited list of projects
    :rtype: Dict{namespace/projectName: Project]
    """

    list_of_projects = data.get('projects', [])
    if len(list_of_projects) > 50:
        abort(400, "Too many projects")
    results = {}
    for project in list_of_projects:
        projects = projects_query(ProjectPermissions.Read, as_admin=False)
        splitted = project.split("/")
        if len(splitted) != 2:
            results[project] = {"error": 404}
            continue
        namespace = splitted[0]
        name = splitted[1]
        result = projects.filter(Project.namespace == namespace, Project.name == name).first()
        if result:
            user_ids = result.access.owners + result.access.writers + result.access.readers
            users_map = {u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()}
            results[project] = ProjectListSchema(context={'users_map': users_map}).dump(result)
        else:
            if not current_user or not current_user.is_authenticated:
                results[project] = {"error": 401}
            else:
                results[project] = {"error": 403}
    return results, 200


def get_projects_by_uuids(uuids):  # noqa: E501
    """Get mergin projects by list of projects ids

    Returns a list of projects filtered by ids # noqa: E501
    :rtype: dict{project.id: project}
    """
    proj_ids = [uuid for uuid in uuids.split(',') if is_valid_uuid(uuid)]
    if len(proj_ids) > 10:
        abort(400, "Too many projects")

    user_ids = []
    projects = projects_query(ProjectPermissions.Read, as_admin=False).filter(Project.id.in_(proj_ids)).all()
    for p in projects:
        user_ids.extend(p.access.owners+p.access.writers+p.access.readers)
    users_map = {u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()}
    data = ProjectListSchema(many=True, context={'users_map': users_map}).dump(projects)
    return data, 200


def get_projects(tags=None, q=None, user=None, flag=None, limit=None):  # noqa: E501
    """List mergin projects.

    Returns limited list of projects, optionally filtered by tags, search query, username.

    :rtype: List[Project]
    """
    projects = projects_query(ProjectPermissions.Read)

    if flag:
        user = User.query.filter_by(username=user).first_or_404() if user else current_user
        if not user.is_anonymous:
            orgs = Organisation.query.with_entities(Organisation.name).filter(
                or_(Organisation.admins.contains([user.id]), Organisation.readers.contains([user.id]),
                    Organisation.writers.contains([user.id]), Organisation.owners.contains([user.id])))
            if flag == 'created':
                projects = projects.filter(Project.creator_id == user.id).filter_by(namespace=user.username)
            if flag == 'shared':
                projects = projects.filter(or_(and_(Project.creator_id != user.id,
                                               Project.access.has(ProjectAccess.readers.contains([user.id]))),  Project.namespace.in_(orgs)))
        else:
            abort(401)
    if tags:
        projects = projects.filter(Project.tags.contains(cast(tags, ARRAY(String))))

    if q:
        projects = projects.filter(Project.name.ilike('%{}%'.format(q)))

    proj_limit = limit if limit and limit < 100 else 100
    projects = projects.options(joinedload(Project.access)).order_by(Project.namespace, Project.name).limit(proj_limit).all()
    # create user map id:username passed to project schema to minimize queries to db
    user_ids = []
    for p in projects:
        user_ids.extend(p.access.owners+p.access.writers+p.access.readers)
    users_map = {u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()}
    sleep(0)  # temporary yield to gevent hub until serialization is fully resolved (#317)
    data = ProjectListSchema(many=True, context={'users_map': users_map}).dump(projects)
    return data, 200


def get_paginated_projects(page, per_page, order_params=None, order_by=None, descending=False, name=None, namespace=None, user=None, flag=None, last_updated_in=None, only_namespace=None, as_admin=False, public=True, only_public=False):  # noqa: E501
    """List mergin projects.

    Returns dictionary with paginated list of projects, optionally filtered by tags, project name, username, namespace, updated date.
    and number of total filtered projects

    :param page:page number
    :param per_page results per page
    :param order_by order by field name -deprecated
    :param descending order of sort -deprecated
    :param order_params fields to sort e.g. name_asc, updated_desc
    :param name filter by project name
    :param namespace filter by project namespace
    :param user Username for 'flag' filter. If not provided, in case that is not provided uses logged user
    :param flag created or shared
    :param: last_updated_in for filter projects by days from last update
    :param only_namespace Filter namespace equality to in contrast with namespace attribute which is determinated to search (like)
    :param as_admin User access as admin
    :param public should return any public project, if false filter only projects where user has explicit read permission to project
    :param only_public should return only public projects

    :rtype: Dictionary{
    projects: List[Project],
    count: Integer
    """
    if only_public:
        projects = Project.query.filter(Project.access.has(public=only_public))
    else:
        projects = projects_query(ProjectPermissions.Read, as_admin=as_admin, public=public)

    if flag:
        user = User.query.filter_by(username=user).first_or_404() if user else current_user
        if not user.is_anonymous:
            if flag == 'created':
                projects = projects.filter(Project.creator_id == user.id).filter_by(namespace=user.username)
            if flag == 'shared':
                orgs = Organisation.query.with_entities(Organisation.name).filter(
                    or_(Organisation.admins.contains([user.id]), Organisation.readers.contains([user.id]),
                        Organisation.writers.contains([user.id]), Organisation.owners.contains([user.id])))
                projects = projects.filter(or_(and_(Project.creator_id != user.id,
                                               Project.access.has(ProjectAccess.readers.contains([user.id]))),  Project.namespace.in_(orgs)))
        else:
            abort(401)

    if name:
        projects = projects.filter(Project.name.ilike('%{}%'.format(name)) | Project.namespace.ilike('%{}%'.format(name)))

    if namespace:
        projects = projects.filter(Project.namespace.ilike('%{}%'.format(namespace)))

    if only_namespace:
        projects = projects.filter(Project.namespace == only_namespace)

    if last_updated_in:
        projects = projects.filter(Project.updated >= datetime.utcnow() - timedelta(days=last_updated_in))

    projects = projects.options(joinedload(Project.access))

    if order_params:
        order_by_params = []
        for p in order_params.split(","):
            string_param = p.strip()
            if "_asc" in string_param:
                string_param = string_param.replace("_asc", "")
                order_by_params.append(Project.__table__.c[string_param].asc())
            elif "_desc" in string_param:
                string_param = string_param.replace("_desc", "")
                order_by_params.append(Project.__table__.c[string_param].desc())
        projects = projects.order_by(*order_by_params)
    elif descending and order_by:
        projects = projects.order_by(desc(Project.__table__.c[order_by]))
    elif not descending and order_by:
        projects = projects.order_by(asc(Project.__table__.c[order_by]))

    result = projects.paginate(page, per_page).items
    total = projects.paginate(page, per_page).total

    # create user map id:username passed to project schema to minimize queries to db
    user_ids = []
    for p in result:
        user_ids.extend(p.access.owners+p.access.writers+p.access.readers)

    users_map = {u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()}
    sleep(0)  # temporary yield to gevent hub until serialization is fully resolved (#317)
    data = ProjectListSchema(many=True, context={'users_map': users_map}).dump(result)
    data = {'projects': data,
            'count': total}
    return data, 200

@auth_required
def update_project(namespace, project_name, data):  # noqa: E501  # pylint: disable=W0613
    """Update an existing project.

     # noqa: E501

    :param project_name: Name of project that need to be updated.
    :type project_name: str
    :param data: Data to be updated.
    :type data: dict | bytes

    :rtype: Project
    """
    project = require_project(namespace, project_name, ProjectPermissions.Update)
    access = data.get('access', {})
    id_diffs = []

    #transform usernames from client to ids
    if "ownersnames" in access:
        owners = User.query.with_entities(User.id).filter(User.username.in_(access['ownersnames'])).all()
        access["owners"] = [w.id for w in owners]
    if "readersnames" in access:
        readers = User.query.with_entities(User.id).filter(User.username.in_(access['readersnames'])).all()
        access["readers"] = [w.id for w in readers]
    if "writersnames" in access:
        writers = User.query.with_entities(User.id).filter(User.username.in_(access['writersnames'])).all()
        access["writers"] = [w.id for w in writers]

    # prevent to remove ownership of project creator
    if 'owners' in access:
        if project.creator_id not in access['owners']:
            abort(400, str('Ownership of project creator cannot be removed.'))

    for key, value in access.items():
        if not hasattr(project.access, key):
            continue
        if isinstance(value, list):
            id_diffs.append(set(value) ^ set(getattr(project.access, key)))
        setattr(project.access, key, value)

    db.session.add(project)
    db.session.commit()

    users_ids = set().union(*id_diffs)
    user_profiles = UserProfile.query.filter(UserProfile.user_id.in_(users_ids)).all()
    project_path = '/'.join([namespace, project.name])
    web_link = f"{request.url_root.strip('/')}/projects/{project_path}"
    for user_profile in user_profiles:
        privileges = []
        if user_profile.user.id in project.access.owners:
            privileges += ['edit', 'remove']
        if user_profile.user.id in project.access.writers:
            privileges.append('upload')
        if user_profile.user.id in project.access.readers:
            privileges.append('download')
        subject = "Project access modified"
        if len(privileges):
            html = render_template('email/modified_project_access.html', subject=subject, project=project, user=user_profile.user,
                                   privileges=privileges, link=web_link)
        else:
            html = render_template('email/removed_project_access.html', subject=subject, project=project, user=user_profile.user)

        if not (user_profile.receive_notifications and user_profile.user.verified_email):
            continue
        email_data = {
            'subject': f'Access to mergin project {project_path} has been modified',
            'html': html,
            'recipients': [user_profile.user.email],
            'sender': current_app.config['MAIL_DEFAULT_SENDER']
        }
        send_email_async.delay(**email_data)

    return ProjectSchema().dump(project), 200


@auth_required
def project_push(namespace, project_name, data):
    """
    Synchronize project data.

    Apply changes in project if no uploads required. Creates upload transaction for added/modified files. # noqa: E501

    :param namespace: Namespace for project to look into.
    :type namespace: str
    :param project_name: Project name.
    :type project_name: str
    :param data: Description of project changes.
    :type data: dict | bytes

    :rtype: None
    """
    version = data.get('version')
    changes = data['changes']
    project = require_project(namespace, project_name, ProjectPermissions.Upload)
    pv = project.versions[0] if project.versions else None
    if pv and pv.name != version:
        abort(400, 'Version mismatch')
    if not pv and version != 'v0':
        abort(400, 'First push should be with v0')

    if all(len(changes[key]) == 0 for key in changes.keys()):
        abort(400, 'No changes')

    # check if same file is not already uploaded
    for item in changes["added"]:
        if not all(ele['path'] != item['path'] for ele in project.files):
            abort(400, 'File {} has been already uploaded'.format(item["path"]))

    # changes' files must be unique
    changes_files = []
    sanitized_files = []
    blacklisted_files = []
    for change in changes.values():
        for f in change:
            if is_file_name_blacklisted(f['path'], current_app.config['BLACKLIST']):
                blacklisted_files.append(f)
            # all file need to be unique after sanitized
            f['sanitized_path'] = mergin_secure_filename(f['path'])
            if f['sanitized_path'] in sanitized_files:
                filename, file_extension = os.path.splitext(f['sanitized_path'])
                f['sanitized_path'] = filename + f'.{str(uuid.uuid4())}' + file_extension
            sanitized_files.append(f['sanitized_path'])
            if 'diff' in f:
                f['diff']['sanitized_path'] = mergin_secure_filename(f['diff']['path'])
                if f['diff']['sanitized_path'] in sanitized_files:
                    filename, file_extension = os.path.splitext(f['diff']['sanitized_path'])
                    f['diff']['sanitized_path'] = filename + f'.{str(uuid.uuid4())}' + file_extension
            changes_files.append(f['path'])
    if len(set(changes_files)) != len(changes_files):
        abort(400, 'Not unique changes')

    # remove blacklisted files from changes
    for key, change in changes.items():
        files_to_upload = [f for f in change if f not in blacklisted_files]
        changes[key] = files_to_upload

    # Convert datetimes to UTC
    for key in changes.keys():
        for f in changes[key]:
            f['mtime'] = datetime.utcnow()

    num_version = int_version(version)

    # Check user data limit
    updates = [f['path'] for f in changes['updated']]
    updated_files = list(filter(lambda i: i['path'] in updates, project.files))
    additional_disk_usage = sum(file['size'] for file in changes['added'] + changes['updated']) - \
                            sum(file['size'] for file in updated_files) - sum(file['size'] for file in changes["removed"])
    ns = Namespace.query.filter_by(name=project.namespace).first()
    if ns.disk_usage() + additional_disk_usage > ns.storage:
        abort(400, 'You have reached a data limit')

    upload = Upload(project, num_version, changes, current_user.id)
    db.session.add(upload)
    try:
        # Creating upload transaction with different project's version is possible.
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # check and clean dangling uploads or abort
        for current_upload in project.uploads.all():
            upload_dir = os.path.join(project.storage.project_dir, 'tmp', current_upload.id)
            upload_lockfile = os.path.join(upload_dir, 'lockfile')
            if os.path.exists(upload_lockfile):
                if time() - os.path.getmtime(upload_lockfile) < current_app.config['LOCKFILE_EXPIRATION']:
                    abort(400, 'Another process is running. Please try later.')
            db.session.delete(current_upload)
            db.session.commit()


        # Try again after cleanup
        db.session.add(upload)
        try:
            db.session.commit()
            move_to_tmp(upload_dir)
        except IntegrityError:
            abort(422, 'Failed to create upload session. Please try later.')

    # Create transaction folder and lockfile
    folder = os.path.join(project.storage.project_dir, "tmp", upload.id)
    os.makedirs(folder)
    open(os.path.join(folder, 'lockfile'), 'w').close()

    # Update immediately without uploading of new/modified files, and remove transaction/lockfile
    if not(changes['added'] or changes['updated']):
        next_version = "v{}".format(num_version + 1)
        project.storage.apply_changes(changes, next_version, upload.id)
        flag_modified(project, 'files')
        project.disk_usage = sum(file['size'] for file in project.files)
        user_agent = get_user_agent(request)
        pv = ProjectVersion(project, next_version, current_user.username, changes, project.files, get_ip(request), user_agent)
        project.latest_version = next_version
        db.session.add(pv)
        db.session.add(project)
        db.session.delete(upload)
        db.session.commit()
        move_to_tmp(folder)
        return jsonify(ProjectSchema().dump(project)), 200

    return {'transaction': upload.id}


@auth_required
def chunk_upload(transaction_id, chunk_id):
    """Upload file chunk as defined in upload transaction.

     # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str
    :param chunk_id: Chunk id.
    :type chunk_id: str

    :rtype: None
    """
    upload, upload_dir = get_upload(transaction_id)
    for f in upload.changes["added"] + upload.changes["updated"]:
        if "chunks" in f and chunk_id in f["chunks"]:
            dest = os.path.join(upload_dir, "chunks", chunk_id)
            lockfile = os.path.join(upload_dir, "lockfile")
            with Toucher(lockfile, 30):
                try:
                    # we could have used request.data here but it could eventually cause OOM issue
                    save_to_file(request.stream, dest, current_app.config['MAX_CHUNK_SIZE'])
                except IOError:
                    move_to_tmp(dest, transaction_id)
                    abort(400, "Too big chunk")
                if os.path.exists(dest):
                    checksum = generate_checksum(dest)
                    size = os.path.getsize(dest)
                    return jsonify({
                        "checksum": checksum,
                        "size": size
                    }), 200
                else:
                    abort(400, 'Upload was probably canceled')
    abort(404)


@auth_required
def push_finish(transaction_id):
    """Finalize project data upload.

    Steps involved in finalization:
     - merge chunks together (if there are some)
     - do integrity check comparing uploaded file sizes with what was expected
     - move uploaded files to new version dir and applying sync changes (e.g. geodiff apply_changeset)
     - bump up version in database
     - remove artifacts (chunks, lockfile) by moving them to tmp directory

    # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    upload, upload_dir = get_upload(transaction_id)
    changes = upload.changes
    upload_files = changes["added"] + changes["updated"]
    project = upload.project
    project_path = os.path.join(project.namespace, project.name)
    corrupted_files = []

    for f in upload_files:
        if "diff" in f:
            dest_file = os.path.join(
                upload_dir, "files", get_path_from_files(
                    upload_files, f["diff"]["path"], is_diff=True))
            expected_size = f["diff"]["size"]
        else:
            dest_file = os.path.join(
                upload_dir, "files",  get_path_from_files(upload_files, f["path"]))
            expected_size = f["size"]
        if "chunks" in f:
            # Concatenate chunks into single file
            # TODO we need to move this elsewhere since it can fail for large files (and slow FS)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with open(dest_file, "wb") as dest:
                try:
                    for chunk_id in f["chunks"]:
                        sleep(0)  # to unblock greenlet
                        chunk_file = os.path.join(upload_dir, "chunks", chunk_id)
                        with open(chunk_file, "rb") as src:
                            data = src.read(8192)
                            while data:
                                dest.write(data)
                                data = src.read(8192)
                except IOError:
                    logging.exception("Failed to process chunk: %s in project %s" % (chunk_id, project_path))
                    corrupted_files.append(f["path"])
                    continue

        if expected_size != os.path.getsize(dest_file):
            logging.error("Data integrity check has failed on file %s in project %s" % (f["path"], project_path), exc_info=True)
            corrupted_files.append(f["path"])

    if corrupted_files:
        move_to_tmp(upload_dir)
        abort(422, {"corrupted_files": corrupted_files})

    next_version = "v{}".format(upload.version + 1)
    files_dir = os.path.join(upload_dir, "files")
    target_dir = os.path.join(project.storage.project_dir, next_version)
    if os.path.exists(target_dir):
        pv = project.versions[0] if project.versions else None
        if pv and pv.name == next_version:
            abort(409, {"There is already version with this name %s" % next_version})
        logging.info("Upload transaction: Target directory already exists. Overwriting %s" % target_dir)
        move_to_tmp(target_dir)

    try:
        # let's move uploaded files where they are expected to be
        os.renames(files_dir, target_dir)
        project.storage.apply_changes(changes, next_version, transaction_id)
        flag_modified(project, "files")
        project.disk_usage = sum(file['size'] for file in project.files)

        user_agent = get_user_agent(request)
        pv = ProjectVersion(project, next_version, current_user.username, changes, project.files, get_ip(request), user_agent)
        project.latest_version = next_version
        db.session.add(pv)
        db.session.add(project)
        db.session.delete(upload)
        db.session.commit()
        # remove artifacts
        move_to_tmp(upload_dir, transaction_id)
    except (psycopg2.Error, FileNotFoundError, DataSyncError) as err:
        move_to_tmp(upload_dir)
        abort(422, "Failed to create new version: {}".format(str(err)))

    project.storage.optimize_storage()
    return jsonify(ProjectSchema().dump(project)), 200


@auth_required
def push_cancel(transaction_id):
    """Cancel upload transaction.

    # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    upload, upload_dir = get_upload(transaction_id)
    db.session.delete(upload)
    db.session.commit()
    move_to_tmp(upload_dir)
    return jsonify({"success": True}), 200


@auth_required
def clone_project(namespace, project_name, destination=None):  # noqa: E501
    """Clone project.

    Clone project to another namespace. Only recent version is copied over and history is lost.
    Destination namespace and project name are optionally set in query parameters
    otherwise request user is used with the same project name as cloned project. # noqa: E501

    :param namespace: Namespace for project to look into.
    :type namespace: str
    :param project_name: Project name.
    :type project_name: str
    :param destination: Destination (namespace and project name) where project should be cloned.
    :type destination: dict | bytes

    :rtype: None
    """
    cloned_project = require_project(namespace, project_name, ProjectPermissions.Read)
    dest_ns = destination.get('namespace', current_user.username).strip()
    dest_project = destination.get('project', cloned_project.name).strip()

    check_access_to_namespace(dest_ns, current_user)

    _project = Project.query.filter_by(name=dest_project, namespace=dest_ns).first()
    if _project:
        abort(409, "Project {}/{} already exists!".format(dest_ns, dest_project))

    p = Project(
        name=dest_project,
        storage_params={"type": "local", "location": generate_location()},
        creator=current_user,
        namespace=dest_ns
    )
    p.updated = datetime.utcnow()
    pa = ProjectAccess(p, public=False)

    try:
        p.storage.initialize(template_project=cloned_project)
    except InitializationError as e:
        abort(400, f"Failed to clone project: {str(e)}")

    version = "v1" if p.files else "v0"
    changes = {"added": p.files, "renamed": [], "updated": [], "removed": []}
    user_agent = get_user_agent(request)
    p.latest_version = version
    version = ProjectVersion(p, version, current_user.username, changes, p.files, get_ip(request), user_agent)
    p.versions.append(version)
    db.session.add(p)
    db.session.add(pa)
    db.session.commit()
    wm.emit_signal(SIG_NEW_PROJECT, request.path, msg=f'New project *{dest_ns}/{dest_project}* has been cloned')
    return NoContent, 200


def get_resource_history(project_name, namespace, path):  # noqa: E501
    """History of project resource (file)

    Lookup in project versions to get history of changes for particular file # noqa: E501

    :param project_name: Project name.
    :type project_name: str
    :param namespace: Namespace project belong to.
    :type namespace: str
    :param path: Path to file in project.
    :type path: str

    :rtype: FileInfo
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    file = next((f for f in project.files if f['path'] == path), None)
    if not file:
        abort(404, path)

    last_version = ProjectVersion.query.filter_by(project_id=project.id).order_by(
        ProjectVersion.created.desc()).first_or_404()
    file['history'] = project.file_history(file['path'], 'v1', last_version.name)
    file_info = FileInfoSchema(context={'project_dir': project.storage.project_dir}).dump(file)
    return file_info, 200


def get_resource_changeset(project_name, namespace, version_id, path):  # noqa: E501
    """ Changeset of the resource (file)

    Calculate geodiff changeset for particular file and particular project version # noqa: E501

    :param project_name: Project name.
    :type project_name: str
    :param namespace: Namespace project belong to.
    :type namespace: str
    :param version_id: Version id of the file.
    :type version_id: str
    :param path: Path to file in project.
    :type path: str

    :rtype: [GeodiffChangeset]
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    if not project:
        abort(404, f"Project {namespace}/{project_name} not found")

    version = ProjectVersion.query.filter_by(project_id=project.id, name=version_id).first()
    if not version:
        abort(404, f"Version {version_id} in project {namespace}/{project_name} not found")

    file = next((f for f in version.files if f['location'] == os.path.join(version_id, path)), None)
    if not file:
        abort(404, f"File {path} not found")

    if 'diff' not in file:
        abort(404, "Diff not found")

    changeset = os.path.join(version.project.storage.project_dir, file['diff']['location'])
    json_file = os.path.join(version.project.storage.project_dir, file['location'] + '-diff-changeset')
    if not os.path.exists(json_file):
        try:
            version.project.storage.geodiff.list_changes(changeset, json_file)
        except GeoDiffLibError as e:
            abort(422, f"Change set could not be calculated: {str(e)}")

    with open(json_file, 'r') as jf:
        content = json.load(jf)
        if 'geodiff' not in content:
            abort(422, "Expected format does not match response from Geodiff")

    return content['geodiff'], 200
