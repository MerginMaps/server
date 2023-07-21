# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import binascii
import functools
import json
import mimetypes
import os
import logging
from typing import Dict
from urllib.parse import quote
import uuid
from time import time
from datetime import datetime
import psycopg2
from blinker import signal
from connexion import NoContent, request
from flask import (
    abort,
    render_template,
    current_app,
    send_from_directory,
    jsonify,
    make_response,
)
from pygeodiff import GeoDiffLibError
from flask_login import current_user
from sqlalchemy import and_, desc, asc, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from binaryornot.check import is_binary
from gevent import sleep
import base64
from werkzeug.exceptions import HTTPException
from .. import db
from ..auth import auth_required
from ..auth.models import User, UserProfile
from .models import Project, ProjectAccess, ProjectVersion, Upload
from .schemas import (
    ProjectSchema,
    ProjectListSchema,
    ProjectVersionSchema,
    FileInfoSchema,
    ProjectSchemaForVersion,
    UserWorkspaceSchema,
)
from .storages.storage import FileNotFound, DataSyncError, InitializationError
from .storages.disk import save_to_file, move_to_tmp
from .permissions import (
    require_project,
    projects_query,
    ProjectPermissions,
    get_upload,
    require_project_by_uuid,
)
from .utils import (
    generate_checksum,
    Toucher,
    int_version,
    is_file_name_blacklisted,
    get_ip,
    get_user_agent,
    generate_location,
    is_valid_uuid,
    gpkg_wkb_to_wkt,
    is_versioned_file,
    is_valid_gpkg,
)
from .utils import (
    is_name_allowed,
    mergin_secure_filename,
    get_path_from_files,
    get_project_path,
)
from ..celery import send_email_async
from ..utils import format_time_delta

push_triggered = signal("push_triggered")
project_version_created = signal("project_version_created")
project_deleted = signal("project_deleted")


def _project_version_files(project, version=None):
    if version:
        pv = ProjectVersion.query.filter_by(
            project_id=project.id, name=version
        ).first_or_404("Project version does not exist")
        return pv.files
    return project.files


def parse_project_access_update_request(access: Dict) -> Dict:
    """Parse raw project access update request and filter out invalid entries.
    New access can be specified either by list of usernames or ids -> convert only to ids fur further processing.

    :Example:

        >>> parse_project_access_update_request({"writersnames": ["john"], "readersnames": ["john, jack, bob.inactive"]})
        {"writers": [1], "readers": [1,2], "invalid_usernames": ["bob.inactive"], "invalid_ids":[]}
        >>> parse_project_access_update_request({"writers": [1], "readers": [1,2,3]})
        {"writers": [1], "readers": [1,2], "invalid_usernames": [], "invalid_ids":[3]"}
    """
    parsed_access = {}
    names = set(
        access.get("ownersnames", [])
        + access.get("writersnames", [])
        + access.get("readersnames", [])
    )
    ids = set(
        access.get("owners", []) + access.get("writers", []) + access.get("readers", [])
    )
    # get only valid user entries from database
    valid_users = (
        db.session.query(User.id, User.username)
        .filter(User.username.in_(list(names)) | User.id.in_(list(ids)))
        .filter(User.active.is_(True))
        .all()
    )
    valid_users_map = {u.username: u.id for u in valid_users}
    valid_usernames = valid_users_map.keys()
    valid_ids = valid_users_map.values()

    for key in ("owners", "writers", "readers"):
        # transform usernames from client request to ids, which has precedence over ids in request
        if key + "names" in access:
            parsed_access[key] = [
                valid_users_map[username]
                for username in access.get(key + "names")
                if username in valid_usernames
            ]
        # use legacy option
        elif key in access:
            parsed_access[key] = [id for id in access.get(key) if id in valid_ids]
    parsed_access["invalid_usernames"] = list(names.difference(valid_usernames))
    parsed_access["invalid_ids"] = list(ids.difference(valid_ids))
    return parsed_access


@auth_required
def add_project(namespace):  # noqa: E501
    """Add a new mergin project to specified workspace

    Add new project to database and create either empty project directory or copy files from template project # noqa: E501

    :param namespace: Workspace for project to look into
    :type namespace: str

    :rtype: None
    """
    request.json["name"] = request.json["name"].strip()

    if not is_name_allowed(request.json["name"]):
        abort(
            400,
            "Please don't start project name with . and use only alphanumeric or these -._! characters in project name.",
        )

    if request.is_json:
        ua = get_user_agent(request)
        workspace = current_app.ws_handler.get_by_name(namespace)
        if not workspace:
            # return special message if former 'user workspace' was used
            if namespace == current_user.username:
                abort(
                    404,
                    "Workspace does not exist. Please try updating to the newest version",
                )
            else:
                abort(404, "Workspace does not exist")
        if not workspace.user_has_permissions(current_user, "admin"):
            abort(403, "You do not have permissions for this workspace")

        proj = Project.query.filter_by(
            name=request.json["name"], workspace_id=workspace.id
        ).first()
        if proj:
            if proj.removed_at:
                msg = (
                    f"Project with the same name is scheduled for deletion, "
                    f"you can create a project with this name in {format_time_delta(proj.expiration)}"
                )
            else:
                msg = "Project with the same name already exists"
            abort(409, msg)

        request.json["storage_params"] = {
            "type": "local",
            "location": generate_location(),
        }

        p = Project(**request.json, creator=current_user, workspace=workspace)
        p.updated = datetime.utcnow()
        pa = ProjectAccess(p, public=request.json.get("public", False))

        template = request.json.get("template", None)
        ip = get_ip(request)
        if template:
            template = (
                Project.query.filter(Project.creator.has(username="TEMPLATES"))
                .filter(Project.name == template)
                .first_or_404()
            )
            try:
                p.storage.initialize(template_project=template)
            except InitializationError as e:
                abort(400, f"Failed to initialize project: {str(e)}")

            version = "v1"
            changes = {"added": p.files, "updated": [], "removed": []}
            user_agent = get_user_agent(request)
            p.latest_version = version
            version = ProjectVersion(
                p,
                version,
                current_user.username,
                changes,
                p.files,
                get_ip(request),
                user_agent,
            )
        else:
            changes = {"added": [], "updated": [], "removed": []}
            version = ProjectVersion(
                p, "v0", current_user.username, changes, [], ip, ua
            )
            p.latest_version = "v0"
            try:
                p.storage.initialize(template_project=template)
            except InitializationError as exc:
                abort(400, f"Failed to initialize project: {str(exc)}")

        db.session.add(p)
        db.session.add(pa)
        version.project = p
        db.session.add(version)
        db.session.commit()
        project_version_created.send(version)
        return NoContent, 200


@auth_required
def delete_project(namespace, project_name):  # noqa: E501
    """Delete a project.

    Remove project - files are temporarily kept for eventual restore and project is only marked for removal.

    :param namespace: Workspace for project to look into
    :type namespace: str
    :param project_name: Project name
    :type project_name: str

    :rtype: None
    """
    project = require_project(namespace, project_name, ProjectPermissions.Delete)
    project.removed_at = datetime.utcnow()
    project.removed_by = current_user.username
    project_deleted.send(project)
    db.session.commit()
    return NoContent, 200


def download_project(
    namespace, project_name, format=None, version=None
):  # noqa: E501 # pylint: disable=W0622
    """Download full project

    Download whole project folder as zip file or multipart stream # noqa: E501

    :param project_name: Name of project to download.
    :type project_name: str
    :param namespace: Workspace for project to look into.
    :type namespace: str
    :param format: Output format (only zip available).
    :type format: str
    :param version: Particular version to download
    :type version: str

    :rtype: file - zip archive or multipart stream with project files
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    files = _project_version_files(project, version)
    total_size = sum(file["size"] for file in files)
    if total_size > current_app.config["MAX_DOWNLOAD_ARCHIVE_SIZE"]:
        abort(
            400,
            "The total size of requested files is too large to download as a single zip, "
            "please use different method/client for download",
        )
    try:
        return project.storage.download_files(files, format, version=version)
    except FileNotFound as e:
        abort(404, str(e))


def download_project_file(
    project_name, namespace, file, version=None, diff=None
):  # noqa: E501
    """Download project file

    Download individual file or its diff file from project. # noqa: E501

    :param project_name: Project name.
    :type project_name: str
    :param namespace: Workspace for project to look into.
    :type namespace: str
    :param file: Path to file.
    :type file: str
    :param version: Version tag.
    :type version: str
    :param diff: Ask for diff file instead of full one.
    :type diff: bool

    :rtype: file
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    files = _project_version_files(project, version)
    file_path = None
    if diff and version:
        # get specific version of geodiff file modified in requested version
        file_obj = next(
            (f for f in files if f["location"] == os.path.join(version, file)), None
        )
        if not file_obj:
            abort(404, file)
        if "diff" not in file_obj:
            abort(404, f"No diff in particular file {file} version")
        file_path = file_obj["diff"]["location"]
    elif diff:
        abort(400, f"Changeset must be requested for particular file version")
    else:
        # get latest version of file
        file_path = next((f["location"] for f in files if f["path"] == file), None)

    if not file_path:
        abort(404, file)

    if version and not diff:
        project.storage.restore_versioned_file(file, version)

    abs_path = os.path.join(project.storage.project_dir, file_path)
    # check file exists (e.g. there might have been issue with restore)
    if not os.path.exists(abs_path):
        logging.error(f"Missing file {namespace}/{project_name}/{file_path}")
        abort(404)

    if current_app.config["USE_X_ACCEL"]:
        # encoding for nginx to be able to download file with non-ascii chars
        encoded_file_path = quote(file_path.encode("utf-8"))
        resp = make_response()
        resp.headers[
            "X-Accel-Redirect"
        ] = f"/download/{project.storage_params['location']}/{encoded_file_path}"
        resp.headers["X-Accel-Buffering"] = True
        resp.headers["X-Accel-Expires"] = "off"
    else:
        resp = send_from_directory(
            os.path.dirname(abs_path), os.path.basename(abs_path)
        )

    if not is_binary(abs_path):
        mime_type = "text/plain"
    else:
        mime_type = mimetypes.guess_type(abs_path)[0]
    resp.headers["Content-Type"] = mime_type
    resp.headers["Content-Disposition"] = "attachment; filename={}".format(
        quote(os.path.basename(file).encode("utf-8"))
    )
    resp.direct_passthrough = False
    return resp


def get_project(project_name, namespace, since="", version=None):  # noqa: E501
    """Find project by name.

    Returns a single project of specified version with details about files including history for versioned files (diffs) if needed. # noqa: E501

    :param namespace: Workspace for project to look into
    :type namespace: str
    :param project_name: Project name
    :type project_name: str
    :param since: Version to look up diff files history from.
    :type since: str
    :param version: Project version. Mutually exclusive with &#39;since&#39;.
    :type version: str

    :rtype: ProjectDetail
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)

    if since and version:
        abort(400, "Parameters 'since' and 'version' are mutually exclusive")
    elif since:
        # append history for versioned files
        for f in project.files:
            f["history"] = project.file_history(
                f["path"], since, project.latest_version
            )
        data = ProjectSchema(exclude=["storage_params"]).dump(project)
    elif version:
        # return project info at requested version
        version_obj = ProjectVersion.query.filter_by(
            project_id=project.id, name=version
        ).first_or_404("Project at requested version does not exist")
        data = ProjectSchemaForVersion().dump(version_obj)
    else:
        # return current project info
        data = ProjectSchema(exclude=["storage_params"]).dump(project)
    return data, 200


def get_project_by_uuid(project_id):  # noqa: E501
    """Find project specified by uuid.

    Returns a single project with details about files including history for versioned files (diffs) if needed. # noqa: E501

    :param project_id: UUID of project to return.
    :type project_id: str

    :rtype: ProjectDetail
    """
    project = require_project_by_uuid(project_id, ProjectPermissions.Read)
    # return current project info
    data = ProjectSchema(exclude=["storage_params"]).dump(project)
    return data, 200


def get_paginated_project_versions(
    page, per_page, namespace, project_name, descending=True
):
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    query = ProjectVersion.query.filter(
        and_(ProjectVersion.project_id == project.id, ProjectVersion.name != "v0")
    )

    if descending:
        query = query.order_by(desc(ProjectVersion.created))
    elif not descending:
        query = query.order_by(asc(ProjectVersion.created))

    result = query.paginate(page, per_page).items
    total = query.paginate(page, per_page).total
    versions = ProjectVersionSchema(exclude=["files"], many=True).dump(result)
    data = {"versions": versions, "count": total}
    return data, 200


def get_projects_by_names():  # noqa: E501
    """List mergin projects specified by list of projects with namespaces and names

    Returns list of requested projects specified by namespaces and names # noqa: E501

    :rtype: Dict[str: ProjectListItem]
    """
    list_of_projects = request.json.get("projects", [])
    if len(list_of_projects) > 50:
        abort(400, "Too many projects")
    results = {}
    for project in list_of_projects:
        projects = projects_query(ProjectPermissions.Read, as_admin=False)
        splitted = project.split("/")
        if len(splitted) != 2:
            results[project] = {"error": 404}
            continue
        ws = splitted[0]
        name = splitted[1]
        workspace = current_app.ws_handler.get_by_name(ws)
        if not workspace:
            results[project] = {"error": 404}
            continue
        result = projects.filter(
            Project.workspace_id == workspace.id, Project.name == name
        ).first()
        if result:
            user_ids = (
                result.access.owners + result.access.writers + result.access.readers
            )
            users_map = {
                u.id: u.username
                for u in User.query.filter(User.id.in_(set(user_ids))).all()
            }
            workspaces_map = {workspace.id: workspace.name}
            ctx = {"users_map": users_map, "workspaces_map": workspaces_map}
            results[project] = ProjectListSchema(context=ctx).dump(result)
        else:
            if not current_user or not current_user.is_authenticated:
                results[project] = {"error": 401}
            else:
                results[project] = {"error": 404}
    return results, 200


def get_projects_by_uuids(uuids):  # noqa: E501
    """Find projects specified by ids

    Returns list of requested projects specified by ids # noqa: E501

    :param uuids: List of requested projects uuids.
    :type uuids: str

    :rtype: Dict[uuid, ProjectListItem]
    """
    proj_ids = [uuid for uuid in uuids.split(",") if is_valid_uuid(uuid)]
    if len(proj_ids) > 10:
        abort(400, "Too many projects")

    user_ids = []
    ws_ids = []
    projects = (
        projects_query(ProjectPermissions.Read, as_admin=False)
        .filter(Project.id.in_(proj_ids))
        .all()
    )
    for p in projects:
        user_ids.extend(p.access.owners + p.access.writers + p.access.readers)
        ws_ids.append(p.workspace_id)
    users_map = {
        u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()
    }
    workspaces_map = {w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)}
    ctx = {"users_map": users_map, "workspaces_map": workspaces_map}
    data = ProjectListSchema(many=True, context=ctx).dump(projects)
    projects_map = {item["id"]: item for item in data}
    return projects_map, 200


def get_paginated_projects(
    page,
    per_page,
    order_params=None,
    order_by=None,
    descending=False,
    name=None,
    namespace=None,
    user=None,
    flag=None,
    last_updated_in=None,
    only_namespace=None,
    as_admin=False,
    public=True,
    only_public=False,
):  # noqa: E501
    """List mergin projects

    Returns paginated list of projects, optionally filtered by tags, search query, username. # noqa: E501

    :param page: page number
    :type page: int
    :param per_page: Number of results per page
    :type per_page: int
    :param order_params: Sorting fields e.g. name_asc,updated_desc
    :type order_params: str
    :param order_by: Order by field - DEPRECATED
    :type order_by: str
    :param descending: Order of sorting - DEPRECATED
    :type descending: bool
    :param namespace: Filter projects with workspaces like a workspace
    :type namespace: str
    :param only_namespace: Filter workspace equality to in contrast with namespace attribute which is determined to search (like)
    :type only_namespace: str
    :param name: Filter projects with names or workspaces with ilike pattern
    :type name: str
    :param user: Username for 'flag' filter. If not provided, it means user executing request.
    :type user: str
    :param last_updated_in: Filter projects by days from last update
    :type last_updated_in: int
    :param flag: Predefined filter flag.
    :type flag: str
    :param as_admin: User access as admin
    :type as_admin: bool
    :param public: Return any public project
    :type public: bool
    :param only_public: Return only public projects
    :type only_public: bool

    :rtype: Dict[str: List[ProjectListItem], str: Integer]
    """
    projects = current_app.ws_handler.filter_projects(
        order_params,
        order_by,
        descending,
        name,
        namespace,
        user,
        flag,
        last_updated_in,
        only_namespace,
        as_admin,
        public,
        only_public,
    )
    result = projects.paginate(page, per_page).items
    total = projects.paginate(page, per_page).total

    # create user map id:username passed to project schema to minimize queries to db
    user_ids = []
    for p in result:
        user_ids.extend(p.access.owners + p.access.writers + p.access.readers)

    users_map = {
        u.id: u.username for u in User.query.filter(User.id.in_(set(user_ids))).all()
    }
    ws_ids = [p.workspace_id for p in projects]
    workspaces_map = {w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)}
    ctx = {"users_map": users_map, "workspaces_map": workspaces_map}
    sleep(
        0
    )  # temporary yield to gevent hub until serialization is fully resolved (#317)
    data = ProjectListSchema(many=True, context=ctx).dump(result)
    data = {"projects": data, "count": total}
    return data, 200


@auth_required
def update_project(namespace, project_name):  # noqa: E501  # pylint: disable=W0613
    """Update an existing project

    Updates 'public' flag and access list for project # noqa: E501

    :param namespace: Workspace for project to look into
    :type namespace: str
    :param project_name: Project name
    :type project_name: str

    :rtype: ProjectDetail
    """
    project = require_project(namespace, project_name, ProjectPermissions.Update)
    access = request.json.get("access", {})

    # prevent to remove ownership of project creator
    if access.get("owners", []):
        if project.creator_id and project.creator_id not in access["owners"]:
            abort(400, str("Ownership of project creator cannot be removed."))

    id_diffs, error = current_app.ws_handler.update_project_members(project, access)

    if not id_diffs and error:
        # nothing was done but there are errors
        return jsonify(error.to_dict()), 422

    if "public" in request.json["access"]:
        project.access.public = request.json["access"]["public"]
        db.session.add(project)
        db.session.commit()

    # send email notifications about changes to users
    user_profiles = UserProfile.query.filter(
        UserProfile.user_id.in_(list(id_diffs))
    ).all()
    project_path = "/".join([namespace, project.name])
    web_link = f"{request.url_root.strip('/')}/projects/{project_path}"
    for user_profile in user_profiles:
        if not (
            user_profile.receive_notifications and user_profile.user.verified_email
        ):
            continue
        privileges = []
        if user_profile.user.id in project.access.owners:
            privileges += ["edit", "remove"]
        if user_profile.user.id in project.access.writers:
            privileges.append("upload")
        if user_profile.user.id in project.access.readers:
            privileges.append("download")
        subject = "Project access modified"
        if len(privileges):
            html = render_template(
                "email/modified_project_access.html",
                subject=subject,
                project=project,
                user=user_profile.user,
                privileges=privileges,
                link=web_link,
            )
        else:
            html = render_template(
                "email/removed_project_access.html",
                subject=subject,
                project=project,
                user=user_profile.user,
            )

        email_data = {
            "subject": f"Access to mergin project {project_path} has been modified",
            "html": html,
            "recipients": [user_profile.user.email],
            "sender": current_app.config["MAIL_DEFAULT_SENDER"],
        }
        send_email_async.delay(**email_data)
    # partial success
    if error:
        return jsonify(**error.to_dict(), project=ProjectSchema().dump(project)), 207
    return ProjectSchema().dump(project), 200


def catch_sync_failure(f):
    """Decorator to catch sync failures in push related endpoints"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPException as e:
            if e.code in [401, 403, 404]:
                raise  # nothing to do, just propagate downstream

            project = request.view_args.get("project", None)
            user_agent = get_user_agent(request)
            error_type = None
            # determine the stage of push transaction where failure occurred from the endpoint name
            if request.endpoint == "/v1.mergin_sync_public_api_controller_project_push":
                error_type = "push_start"
            elif (
                request.endpoint == "/v1.mergin_sync_public_api_controller_push_finish"
            ):
                error_type = "push_finish"
            elif request.endpoint == "chunk_upload":
                error_type = "chunk_upload"

            if project:
                project.sync_failed(user_agent, error_type, str(e.description))
            else:
                logging.warning("Missing project info in sync failure")

            raise

    return wrapper


@auth_required
@catch_sync_failure
def project_push(namespace, project_name):
    """Synchronize project data.

    Apply changes in project if no uploads required. Creates upload transaction for added/modified files. # noqa: E501

    :param namespace: Workspace for project to look into.
    :type namespace: str
    :param project_name: Project name.
    :type project_name: str

    :rtype: None or Dict[str: uuid]
    """
    version = request.json["version"]
    changes = request.json["changes"]
    project = require_project(namespace, project_name, ProjectPermissions.Upload)
    request.view_args[
        "project"
    ] = project  # pass full project object to request for later use
    push_triggered.send(project)
    pv = ProjectVersion.query.filter_by(
        project_id=project.id, name=project.latest_version
    ).first()
    if pv and pv.name != version:
        abort(400, "Version mismatch")
    if not pv and version != "v0":
        abort(400, "First push should be with v0")

    if all(len(changes[key]) == 0 for key in changes.keys()):
        abort(400, "No changes")

    # check if same file is not already uploaded
    for item in changes["added"]:
        if not all(ele["path"] != item["path"] for ele in project.files):
            abort(400, "File {} has been already uploaded".format(item["path"]))

    # changes' files must be unique
    changes_files = []
    sanitized_files = []
    blacklisted_files = []
    for change in changes.values():
        for f in change:
            # check if .gpkg file is valid
            if is_versioned_file(f["path"]):
                if not is_valid_gpkg(f):
                    abort(400, "File {} is not valid".format(f["path"]))
            if is_file_name_blacklisted(f["path"], current_app.config["BLACKLIST"]):
                blacklisted_files.append(f)
            # all file need to be unique after sanitized
            f["sanitized_path"] = mergin_secure_filename(f["path"])
            if f["sanitized_path"] in sanitized_files:
                filename, file_extension = os.path.splitext(f["sanitized_path"])
                f["sanitized_path"] = (
                    filename + f".{str(uuid.uuid4())}" + file_extension
                )
            sanitized_files.append(f["sanitized_path"])
            if "diff" in f:
                f["diff"]["sanitized_path"] = mergin_secure_filename(f["diff"]["path"])
                if f["diff"]["sanitized_path"] in sanitized_files:
                    filename, file_extension = os.path.splitext(
                        f["diff"]["sanitized_path"]
                    )
                    f["diff"]["sanitized_path"] = (
                        filename + f".{str(uuid.uuid4())}" + file_extension
                    )
            changes_files.append(f["path"])
    if len(set(changes_files)) != len(changes_files):
        abort(400, "Not unique changes")

    # remove blacklisted files from changes
    for key, change in changes.items():
        files_to_upload = [f for f in change if f not in blacklisted_files]
        changes[key] = files_to_upload

    # Convert datetimes to UTC
    for key in changes.keys():
        for f in changes[key]:
            f["mtime"] = datetime.utcnow()

    num_version = int_version(version)

    # Check user data limit
    updates = [f["path"] for f in changes["updated"]]
    updated_files = list(filter(lambda i: i["path"] in updates, project.files))
    additional_disk_usage = (
        sum(file["size"] for file in changes["added"] + changes["updated"])
        - sum(file["size"] for file in updated_files)
        - sum(file["size"] for file in changes["removed"])
    )
    ws = project.workspace
    if not ws:
        abort(404)

    if ws.disk_usage() + additional_disk_usage > ws.storage:
        abort(400, "You have reached a data limit")

    upload = Upload(project, num_version, changes, current_user.id)
    db.session.add(upload)
    try:
        # Creating upload transaction with different project's version is possible.
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # check and clean dangling uploads or abort
        for current_upload in project.uploads.all():
            upload_dir = os.path.join(
                project.storage.project_dir, "tmp", current_upload.id
            )
            upload_lockfile = os.path.join(upload_dir, "lockfile")
            if os.path.exists(upload_lockfile):
                if (
                    time() - os.path.getmtime(upload_lockfile)
                    < current_app.config["LOCKFILE_EXPIRATION"]
                ):
                    abort(400, "Another process is running. Please try later.")
            db.session.delete(current_upload)
            db.session.commit()
            # previous push attempt is definitely lost
            project.sync_failed(
                "", "push_lost", "Push artefact removed by subsequent push"
            )

        # Try again after cleanup
        db.session.add(upload)
        try:
            db.session.commit()
            move_to_tmp(upload_dir)
        except IntegrityError as err:
            logging.error(f"Failed to create upload session: {str(err)}")
            abort(422, "Failed to create upload session. Please try later.")

    # Create transaction folder and lockfile
    folder = os.path.join(project.storage.project_dir, "tmp", upload.id)
    os.makedirs(folder)
    open(os.path.join(folder, "lockfile"), "w").close()

    # Update immediately without uploading of new/modified files, and remove transaction/lockfile
    if not (changes["added"] or changes["updated"]):
        next_version = "v{}".format(num_version + 1)
        project.storage.apply_changes(changes, next_version, upload.id)
        flag_modified(project, "files")
        project.disk_usage = sum(file["size"] for file in project.files)
        user_agent = get_user_agent(request)
        pv = ProjectVersion(
            project,
            next_version,
            current_user.username,
            changes,
            project.files,
            get_ip(request),
            user_agent,
        )
        project.latest_version = next_version
        db.session.add(pv)
        db.session.add(project)
        db.session.delete(upload)
        db.session.commit()
        project_version_created.send(pv)
        move_to_tmp(folder)
        return jsonify(ProjectSchema().dump(project)), 200

    return {"transaction": upload.id}


@auth_required
@catch_sync_failure
def chunk_upload(transaction_id, chunk_id):
    """Upload file chunk as defined in upload transaction.

     # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str
    :param chunk_id: Chunk id.
    :type chunk_id: str

    :rtype: Dict
    """
    upload, upload_dir = get_upload(transaction_id)
    request.view_args["project"] = upload.project
    for f in upload.changes["added"] + upload.changes["updated"]:
        if "chunks" in f and chunk_id in f["chunks"]:
            dest = os.path.join(upload_dir, "chunks", chunk_id)
            lockfile = os.path.join(upload_dir, "lockfile")
            with Toucher(lockfile, 30):
                try:
                    # we could have used request.data here, but it could eventually cause OOM issue
                    save_to_file(
                        request.stream, dest, current_app.config["MAX_CHUNK_SIZE"]
                    )
                except IOError:
                    move_to_tmp(dest, transaction_id)
                    abort(400, "Too big chunk")
                if os.path.exists(dest):
                    checksum = generate_checksum(dest)
                    size = os.path.getsize(dest)
                    return jsonify({"checksum": checksum, "size": size}), 200
                else:
                    abort(400, "Upload was probably canceled")
    abort(404)


@auth_required
@catch_sync_failure
def push_finish(transaction_id):
    """Finalize project data upload.

    Steps involved in finalization:
     - merge chunks together (if there are some)
     - do integrity check comparing uploaded file sizes with what was expected
     - move uploaded files to new version dir and applying sync changes (e.g. geodiff apply_changeset)
     - bump up version in database
     - remove artifacts (chunks, lockfile) by moving them to tmp directory

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    from .tasks import optimize_storage

    upload, upload_dir = get_upload(transaction_id)
    request.view_args["project"] = upload.project
    changes = upload.changes
    upload_files = changes["added"] + changes["updated"]
    project = upload.project
    project_path = get_project_path(project)
    corrupted_files = []

    for f in upload_files:
        if "diff" in f:
            dest_file = os.path.join(
                upload_dir,
                "files",
                get_path_from_files(upload_files, f["diff"]["path"], is_diff=True),
            )
            expected_size = f["diff"]["size"]
        else:
            dest_file = os.path.join(
                upload_dir, "files", get_path_from_files(upload_files, f["path"])
            )
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
                    logging.exception(
                        "Failed to process chunk: %s in project %s"
                        % (chunk_id, project_path)
                    )
                    corrupted_files.append(f["path"])
                    continue

        if expected_size != os.path.getsize(dest_file):
            logging.error(
                "Data integrity check has failed on file %s in project %s"
                % (f["path"], project_path),
                exc_info=True,
            )
            # check if .gpkg file is valid
            if is_versioned_file(dest_file):
                if not is_valid_gpkg(f):
                    corrupted_files.append(f["path"])
            corrupted_files.append(f["path"])

    if corrupted_files:
        move_to_tmp(upload_dir)
        abort(422, {"corrupted_files": corrupted_files})

    next_version = "v{}".format(upload.version + 1)
    files_dir = os.path.join(upload_dir, "files")
    target_dir = os.path.join(project.storage.project_dir, next_version)
    if os.path.exists(target_dir):
        pv = ProjectVersion.query.filter_by(
            project_id=project.id, name=project.latest_version
        ).first()
        if pv and pv.name == next_version:
            abort(409, {"There is already version with this name %s" % next_version})
        logging.info(
            "Upload transaction: Target directory already exists. Overwriting %s"
            % target_dir
        )
        move_to_tmp(target_dir)

    try:
        # let's move uploaded files where they are expected to be
        os.renames(files_dir, target_dir)
        project.storage.apply_changes(changes, next_version, transaction_id)
        flag_modified(project, "files")
        project.disk_usage = sum(file["size"] for file in project.files)
        user_agent = get_user_agent(request)
        pv = ProjectVersion(
            project,
            next_version,
            current_user.username,
            changes,
            project.files,
            get_ip(request),
            user_agent,
        )
        project.latest_version = next_version
        db.session.add(pv)
        db.session.add(project)
        db.session.delete(upload)
        db.session.commit()
        project_version_created.send(pv)
        # remove artifacts
        move_to_tmp(upload_dir, transaction_id)
    except (psycopg2.Error, FileNotFoundError, DataSyncError) as err:
        move_to_tmp(upload_dir)
        abort(422, "Failed to create new version: {}".format(str(err)))

    num_version = int_version(project.latest_version)
    # do not optimize on every version, every 10th is just fine
    if not num_version % 10:
        optimize_storage.delay(project.id)
    return jsonify(ProjectSchema().dump(project)), 200


@auth_required
def push_cancel(transaction_id):
    """Cancel upload transaction

    Cancel ongoing upload. Uploaded files are removed and another upload can be started. # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    upload, upload_dir = get_upload(transaction_id)
    db.session.delete(upload)
    db.session.commit()
    move_to_tmp(upload_dir)
    return NoContent, 200


@auth_required
def clone_project(namespace, project_name):  # noqa: E501
    """Clone project.

    Clone project. Only recent version is copied over and history is lost.
    Destination workspace and project name are optionally set in query parameters
    otherwise request user is used with the same project name as cloned project. # noqa: E501

    :param namespace: Workspace for project to look into
    :type namespace: str
    :param project_name: Project name
    :type project_name: str

    :rtype: None
    """
    cloned_project = require_project(namespace, project_name, ProjectPermissions.Read)
    cloned_project_workspace = cloned_project.workspace
    cp_workspace_name = cloned_project_workspace.name
    dest_ns = request.json.get("namespace", cp_workspace_name).strip()
    dest_project = request.json.get("project", cloned_project.name).strip()
    ws = current_app.ws_handler.get_by_name(dest_ns)
    if not ws:
        if dest_ns == current_user.username:
            abort(
                404,
                "Workspace does not exist. Please try updating to the newest version",
            )
        else:
            abort(404, "Workspace does not exist")
    if not ws.user_has_permissions(current_user, "admin"):
        abort(403, "You do not have permissions for this workspace")

    if not is_name_allowed(dest_project):
        abort(
            400,
            "Please don't start project name with . and use only alphanumeric or these -._! characters in project name.",
        )

    _project = Project.query.filter_by(name=dest_project, workspace_id=ws.id).first()
    if _project:
        if _project.removed_at:
            msg = (
                f"Project with the same name is scheduled for deletion, "
                f"you can create a project with this name in {format_time_delta(_project.expiration)}"
            )
        else:
            msg = "Project with the same name already exists"
        abort(409, msg)

    p = Project(
        name=dest_project,
        storage_params={"type": "local", "location": generate_location()},
        creator=current_user,
        workspace=ws,
    )
    p.updated = datetime.utcnow()
    pa = ProjectAccess(p, public=False)

    try:
        p.storage.initialize(template_project=cloned_project)
    except InitializationError as e:
        abort(400, f"Failed to clone project: {str(e)}")

    version = "v1" if p.files else "v0"
    changes = {"added": p.files, "updated": [], "removed": []}
    user_agent = get_user_agent(request)
    p.latest_version = version
    version = ProjectVersion(
        p, version, current_user.username, changes, p.files, get_ip(request), user_agent
    )
    db.session.add(p)
    db.session.add(pa)
    version.project = p
    db.session.add(version)
    db.session.commit()
    project_version_created.send(version)
    return NoContent, 200


def get_resource_history(project_name, namespace, path):  # noqa: E501
    """History of project resource (file) changes

    Lookup in project versions to get history of changes for particular file # noqa: E501

    :param project_name: Project name
    :type project_name: str
    :param namespace: Workspace for project to look into
    :type namespace: str
    :param path: Path to file in project
    :type path: str

    :rtype: HistoryFileInfo
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)

    # get the metadata of file at latest version where file is present
    sql = text(
        "SELECT expanded.name, expanded.files AS file FROM "
        "(SELECT pv.name, pv.created, jsonb_array_elements(pv.files) AS files "
        "FROM project_version pv "
        "WHERE files @> :json AND project_id = :project_id) AS expanded "
        "WHERE expanded.files @> :json2 "
        "ORDER BY expanded.created DESC "
        "LIMIT 1;"
    )

    # in query we need exact format including correct quotes for search in jsonb like this '[{"path": "data.gpkg"}]'
    # but because of sqlalchemy params formatting issues we construct json clause manually
    json_query = '[{"path": "' + path + '"}]'
    json2_query = '{"path": "' + path + '"}'
    result = db.session.execute(
        sql, {"project_id": project.id, "json": json_query, "json2": json2_query}
    ).fetchall()
    if not result:
        abort(404, f"File {path} not found")

    file = result[0].file
    file["history"] = project.file_history(path, "v1", project.latest_version)
    file_info = FileInfoSchema(
        context={"project_dir": project.storage.project_dir}
    ).dump(file)
    return file_info, 200


def get_resource_changeset(project_name, namespace, version_id, path):  # noqa: E501
    """Changeset of the resource (file)

    Calculate geodiff changeset for particular project file in particular version # noqa: E501

    :param project_name: Project name
    :type project_name: str
    :param namespace: Workspace for project to look into
    :type namespace: str
    :param version_id: Version id of the file.
    :type version_id: str
    :param path: Path to file in project
    :type path: str

    :rtype: List[GeodiffChangeset]
    """
    project = require_project(namespace, project_name, ProjectPermissions.Read)
    if not project:
        abort(404, f"Project {namespace}/{project_name} not found")

    version = ProjectVersion.query.filter_by(
        project_id=project.id, name=version_id
    ).first()
    if not version:
        abort(
            404, f"Version {version_id} in project {namespace}/{project_name} not found"
        )

    file = next(
        (f for f in version.files if f["location"] == os.path.join(version_id, path)),
        None,
    )
    if not file:
        abort(404, f"File {path} not found")

    if "diff" not in file:
        abort(404, "Diff not found")

    changeset = os.path.join(
        version.project.storage.project_dir, file["diff"]["location"]
    )
    json_file = os.path.join(
        version.project.storage.project_dir, file["location"] + "-diff-changeset"
    )
    basefile = os.path.join(version.project.storage.project_dir, file["location"])
    schema_file = os.path.join(
        version.project.storage.project_dir, file["location"] + "-schema"
    )
    project.storage.flush_geodiff_logger()  # clean geodiff logger

    try:
        if not os.path.exists(basefile):
            version.project.storage.restore_versioned_file(path, version_id)
        if not os.path.exists(json_file):
            version.project.storage.geodiff.list_changes(changeset, json_file)
        if not os.path.exists(schema_file):
            version.project.storage.geodiff.schema("sqlite", "", basefile, schema_file)
    except GeoDiffLibError:
        abort(
            422,
            f"Change set could not be calculated: {project.storage.gediff_log.getvalue()}",
        )

    with open(json_file, "r") as jf:
        content = json.load(jf)

    with open(schema_file, "r") as sf:
        schema = json.load(sf)

    if "geodiff" not in content or "geodiff_schema" not in schema:
        abort(422, "Expected format does not match response from Geodiff")

    # response from geodiff returns geometry in wkb format (with gpkg header), let's convert it to wkt
    for item in content["geodiff"]:
        schema_table = next(
            (t for t in schema["geodiff_schema"] if t["table"] == item["table"]), None
        )
        if not schema_table:
            # this should not happen if gpkg structure was not changed
            abort(422, "Changes cannot be mapped onto table structure")

        for change in item["changes"]:
            col_index = change["column"]
            change["name"] = schema_table["columns"][col_index]["name"]
            change["type"] = schema_table["columns"][col_index]["type"]

        cols_types = [c["type"] for c in schema_table["columns"]]
        if "geometry" not in cols_types:
            continue

        # patch geom changes from wkb to wkt
        geom_col_idx = cols_types.index("geometry")
        geom_change = next(
            (change for change in item["changes"] if change["column"] == geom_col_idx),
            None,
        )
        if not geom_change:
            continue

        try:
            # we are basically looking for 'old', 'new' attributes of change
            for key in ("old", "new"):
                if key not in geom_change:
                    continue
                gpkg_wkb = base64.b64decode(geom_change[key], validate=True)
                wkt = gpkg_wkb_to_wkt(gpkg_wkb)
                if wkt:
                    geom_change[key] = wkt
        except (binascii.Error, TypeError, ValueError):
            continue  # no base64 encoded value
    return content["geodiff"], 200


@auth_required
def user_workspaces():
    """Get list of workspaces available for session user

    :rtype: Workspace
    """
    workspaces = current_app.ws_handler.list_user_workspaces(current_user.username)
    ctx = {"user": current_user}
    data = UserWorkspaceSchema(many=True, context=ctx).dump(workspaces)
    return data, 200


@auth_required
def get_workspace_by_id(id):
    """Return workspace specified by id

    :param id: workspace id
    :type id: str
    :rtype: WorkspaceSchema
    """
    ws = current_app.ws_handler.get(id)
    if not (ws and ws.is_active):
        abort(404, "Workspace not found")

    if not (
        ws.user_has_permissions(current_user, "read")
        or ws.get_user_role(current_user) == "guest"
    ):
        abort(403, f"You do not have permissions to workspace")

    ctx = {"user": current_user}
    data = UserWorkspaceSchema(context=ctx).dump(ws)
    return data, 200


@auth_required
def get_project_version(project_id: str, version: str):
    """Get project version by its name (e.g. v3)"""
    project = require_project_by_uuid(project_id, ProjectPermissions.Read)
    pv = ProjectVersion.query.filter_by(
        project_id=project.id, name=version
    ).first_or_404()
    data = ProjectVersionSchema(exclude=["files"]).dump(pv)
    return data, 200
