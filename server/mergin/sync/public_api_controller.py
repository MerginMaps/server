# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import binascii
import functools
import json
import os
import logging
from dataclasses import asdict
from enum import Enum
from typing import Dict
from datetime import datetime

import gevent
from marshmallow import ValidationError
import psycopg2
from connexion import NoContent, request
from flask import (
    abort,
    current_app,
    jsonify,
    make_response,
)
from pygeodiff import GeoDiffLibError
from flask_login import current_user
import re
from sqlalchemy import and_, desc, asc, text, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import contains_eager, joinedload, load_only, selectinload
from gevent import sleep
import base64
from werkzeug.exceptions import HTTPException, Conflict

from mergin.sync.forms import project_name_validation
from .interfaces import WorkspaceRole
from ..app import db
from ..auth import auth_required
from ..auth.models import User
from .models import (
    FileSyncErrorType,
    FileDiff,
    Project,
    ProjectVersion,
    Upload,
    PushChangeType,
    FileHistory,
    ProjectFilePath,
    ProjectUser,
    ProjectRole,
    project_version_created,
    push_finished,
)
from .files import (
    ProjectFileChange,
    ChangesSchema,
    ProjectFileSchema,
    files_changes_from_upload,
    mergin_secure_filename,
)
from .schemas import (
    ProjectSchema,
    ProjectListSchema,
    ProjectVersionSchema,
    ProjectSchemaForVersion,
    UserWorkspaceSchema,
    FileHistorySchema,
    ProjectVersionListSchema,
)
from .storages.storage import InitializationError
from .storages.disk import save_to_file, move_to_tmp
from .permissions import (
    require_project,
    projects_query,
    ProjectPermissions,
    get_upload_or_fail,
    require_project_by_uuid,
)
from .utils import (
    generate_checksum,
    get_ip,
    get_user_agent,
    generate_location,
    is_valid_uuid,
    get_device_id,
    is_versioned_file,
    prepare_download_response,
    get_device_id,
    wkb2wkt,
)
from .errors import StorageLimitHit, ProjectLocked
from ..utils import format_time_delta


def parse_project_access_update_request(access: Dict) -> Dict:
    """Parse raw project access update request and filter out invalid entries.
    New access can be specified either by list of usernames or ids -> convert only to ids fur further processing.
    Converted lists are flattened, e.g. user id is unique within all keys. Bear in mind roles keys are optional,
    if missing, it means that we do not want to do any changes there.

    Deprecated. Used only in legacy PUT /v1/project endpoint for project access replacement.

    :Example:

        >>> parse_project_access_update_request({"writersnames": ["john"], "readersnames": ["john, jack, bob.inactive"]})
        {"ProjectRole.WRITER": [1], "ProjectRole.READER": [2], "invalid_usernames": ["bob.inactive"], "invalid_ids":[]}
        >>> parse_project_access_update_request({"writers": [1], "readers": [1,2,3]})
        {"ProjectRole.WRITER": [1], "ProjectRole.READER": [2], "invalid_usernames": [], "invalid_ids":[3]"}
    """
    resp = {}
    parsed_access = {}
    names = set(
        access.get("ownersnames", [])
        + access.get("writersnames", [])
        + access.get("editorsnames", [])
        + access.get("readersnames", [])
    )
    ids = set(
        access.get("owners", [])
        + access.get("writers", [])
        + access.get("editors", [])
        + access.get("readers", [])
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

    for key in ("owners", "writers", "editors", "readers"):
        # transform usernames from client request to ids, which has precedence over ids in request
        name_key = key + "names"
        if name_key in access:
            parsed_access[key] = [
                valid_users_map[username]
                for username in access.get(name_key)
                if username in valid_usernames
            ]
        # use legacy option
        elif key in access:
            parsed_access[key] = [id for id in access.get(key) if id in valid_ids]

    # remove 'inheritance', prepare final map for direct assignments
    processed_ids = []
    for key in ("owners", "writers", "editors", "readers"):
        # we might not want to modify all roles
        if key not in parsed_access:
            continue
        role = ProjectRole(key[:-1])
        resp[role] = []
        for user_id in parsed_access.get(key):
            if user_id not in processed_ids:
                resp[role].append(user_id)
                processed_ids.append(user_id)

    resp["invalid_usernames"] = list(names.difference(valid_usernames))
    resp["invalid_ids"] = list(ids.difference(valid_ids))
    return resp


@auth_required
def add_project(namespace):  # noqa: E501
    """Add a new mergin project to specified workspace

    Add new project to database and create either empty project directory or copy files from template project # noqa: E501

    :param namespace: Workspace for project to look into
    :type namespace: str

    :rtype: None
    """
    request.json["name"] = request.json["name"].strip()

    validation_error = project_name_validation(request.json["name"])
    if validation_error:
        abort(
            400,
            validation_error,
        )

    if request.is_json:
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

        p = Project(
            **request.json,
            creator=current_user,
            workspace=workspace,
        )
        p.updated = datetime.utcnow()

        template_name = request.json.get("template", None)
        if template_name:
            template = (
                Project.query.filter(Project.creator.has(username="TEMPLATES"))
                .filter(Project.name == template_name)
                .first_or_404()
            )
            version_name = 1
            file_changes = []
            for file in template.files:
                file_changes.append(
                    ProjectFileChange(
                        file.path,
                        file.checksum,
                        file.size,
                        diff=None,
                        mtime=None,
                        location=os.path.join("v1", mergin_secure_filename(file.path)),
                        change=PushChangeType.CREATE,
                    )
                )

        else:
            template = None
            version_name = 0
            file_changes = []

        try:
            p.storage.initialize(template_project=template)
        except InitializationError as e:
            abort(400, f"Failed to initialize project: {str(e)}")

        version = ProjectVersion(
            p,
            version_name,
            current_user.id,
            file_changes,
            get_ip(request),
            get_user_agent(request),
            get_device_id(request),
        )

        db.session.add(p)
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
    project.removed_by = current_user.id
    db.session.commit()
    return NoContent, 200


class DowloadFileAction(Enum):
    FULL = "full"
    FULL_GPKG = "full_gpkg"
    DIFF = "diff"


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
    if not is_versioned_file(file):
        action = DowloadFileAction.FULL
    elif diff:
        action = DowloadFileAction.DIFF
    else:
        action = DowloadFileAction.FULL_GPKG

    if action is DowloadFileAction.DIFF and not version:
        abort(400, f"Changeset must be requested for particular file version")

    if action is DowloadFileAction.FULL and diff is True:
        abort(404, f"No diff in particular file {file})")

    project = require_project(namespace, project_name, ProjectPermissions.Read)
    lookup_version = (
        ProjectVersion.from_v_name(version) if version else project.latest_version
    )
    # find the latest file change record for version of interest
    fh = (
        FileHistory.query.join(ProjectFilePath)
        .filter(
            ProjectFilePath.project_id == project.id,
            FileHistory.project_version_name <= lookup_version,
            ProjectFilePath.path == file,
        )
        .order_by(FileHistory.project_version_name.desc())
        .first()
    )
    # in case last change was 'delete', file does not exist for such version
    if not fh or fh.change == PushChangeType.DELETE.value:
        abort(404, f"File {file} not found")

    # user asked for diff, but there is no diff at that version
    if action is DowloadFileAction.DIFF and not fh.diff:
        abort(404, f"No diff in particular file {file} version")

    file_path = (
        fh.diff_file.location if action is DowloadFileAction.DIFF else fh.location
    )
    abs_path = os.path.join(project.storage.project_dir, file_path)

    if not os.path.exists(abs_path):
        if action is DowloadFileAction.FULL_GPKG:
            project.storage.restore_versioned_file(
                file, ProjectVersion.from_v_name(version)
            )

            # check again after restore
            if not os.path.exists(abs_path):
                logging.error(
                    f"Failed to restore {namespace}/{project_name}/{file_path}"
                )
                abort(404)
        else:
            logging.error(f"Missing file {namespace}/{project_name}/{file_path}")
            abort(404)

    response = prepare_download_response(project.storage.project_dir, file_path)
    return response


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
        data = ProjectSchema(exclude=["storage_params"]).dump(project)
        since_version = ProjectVersion.from_v_name(since)
        versioned_paths = [f.path for f in project.files if is_versioned_file(f.path)]

        # load history for all versioned files in one query; only the columns
        # actually used downstream are fetched from the joined tables
        all_history = (
            FileHistory.query.join(ProjectFilePath)
            .join(FileHistory.version)
            .options(
                contains_eager(FileHistory.file).load_only(
                    ProjectFilePath.path, ProjectFilePath.project_id
                ),
                contains_eager(FileHistory.version).load_only(ProjectVersion.name),
            )
            .filter(
                ProjectFilePath.project_id == project.id,
                FileHistory.project_version_name.between(
                    since_version, project.latest_version
                ),
                ProjectFilePath.path.in_(versioned_paths),
            )
            .order_by(FileHistory.file_path_id, desc(FileHistory.project_version_name))
            .all()
        )

        # partition by file and apply stop-at-CREATE logic, matching FileHistory.changes behaviour
        history_by_file: dict = {}
        for item in all_history:
            fid = item.file_path_id
            file_history = history_by_file.setdefault(fid, [])
            if file_history and file_history[-1].change in (
                PushChangeType.CREATE.value,
                PushChangeType.DELETE.value,
            ):
                continue
            file_history.append(item)

        # batch-load all FileDiff records needed across all files in one query
        update_diff_items = [
            i
            for items in history_by_file.values()
            for i in items
            if i.change == PushChangeType.UPDATE_DIFF.value
        ]
        if update_diff_items:
            diffs = FileDiff.query.filter(
                FileDiff.file_path_id.in_({i.file_path_id for i in update_diff_items}),
                FileDiff.rank == 0,
                FileDiff.version.in_(
                    [i.project_version_name for i in update_diff_items]
                ),
            ).all()
            diff_map = {(d.file_path_id, d.version): d for d in diffs}
            for item in update_diff_items:
                item.__dict__["diff"] = diff_map.get(
                    (item.file_path_id, item.project_version_name)
                )

        path_to_file_id = {i.file.path: i.file_path_id for i in all_history}
        files = []
        for f in project.files:
            history_field = {}
            if is_versioned_file(f.path):
                for item in history_by_file.get(path_to_file_id.get(f.path), []):
                    history_field[ProjectVersion.to_v_name(item.version.name)] = (
                        FileHistorySchema(exclude=("mtime", "expiration")).dump(item)
                    )
            files.append({**asdict(f), "history": history_field})
        data["files"] = files
    elif version:
        # return project info at requested version
        version_obj = ProjectVersion.query.filter_by(
            project_id=project.id, name=ProjectVersion.from_v_name(version)
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
        and_(ProjectVersion.project_id == project.id, ProjectVersion.name != 0)
    ).options(
        joinedload(ProjectVersion.project).load_only(Project.name, Project.workspace_id)
    )
    query = (
        query.order_by(desc(ProjectVersion.name))
        if descending
        else query.order_by(asc(ProjectVersion.name))
    )
    paginate = query.paginate(page=page, per_page=per_page)
    result = paginate.items
    total = paginate.total

    # batch-resolve workspace names for the page
    ws_ids = {v.project.workspace_id for v in result}
    workspaces_map = {w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)}

    # batch-compute change counts for all versions in the page in one query
    if result:
        version_ids = [v.id for v in result]
        rows = db.session.execute(
            text(
                "SELECT version_id, change, COUNT(change) AS cnt"
                " FROM file_history"
                " WHERE version_id = ANY(:ids)"
                " GROUP BY version_id, change"
            ),
            {"ids": version_ids},
        ).fetchall()
        counts_map = {}
        for row in rows:
            counts_map.setdefault(row.version_id, {})[row.change] = row.cnt
        for v in result:
            v.__dict__["_changes_count"] = counts_map.get(v.id, {})

    ctx = {"workspaces_map": workspaces_map}
    versions = ProjectVersionListSchema(many=True, context=ctx).dump(result)
    data = {"versions": versions, "count": total}
    return data, 200


def _precompute_has_conflict(projects):
    """Pre-populate _has_conflict on each project using a single SQL query."""
    if not projects:
        return
    conflict_regex = r"(\.gpkg|\.qgs|.qgz)(.*conflict.*)|( \(.*conflict.*)"
    rows = db.session.execute(
        text(
            """
            SELECT DISTINCT lpf.project_id
            FROM latest_project_files lpf
            CROSS JOIN unnest(lpf.file_history_ids) AS fh_id
            JOIN file_history fh ON fh.id = fh_id
            JOIN project_file_path fp ON fp.id = fh.file_path_id
            WHERE lpf.project_id = ANY(:project_ids)
            AND fp.path ~ :pattern
        """
        ),
        {"project_ids": [p.id for p in projects], "pattern": conflict_regex},
    ).fetchall()
    conflict_ids = {row.project_id for row in rows}
    for p in projects:
        p.__dict__["_has_conflict"] = p.id in conflict_ids


def get_projects_by_names():  # noqa: E501
    """List mergin projects specified by list of projects with namespaces and names

    Returns list of requested projects specified by namespaces and names # noqa: E501

    :rtype: Dict[str: ProjectListItem]
    """
    list_of_projects = request.json.get("projects", [])
    if len(list_of_projects) > 50:
        abort(400, "Too many projects")

    # batch-resolve workspaces by name (one DB query for DB-backed handlers)
    unique_ws_names = {
        key.split("/")[0] for key in list_of_projects if len(key.split("/")) == 2
    }
    workspaces_by_name = {
        ws.name: ws for ws in current_app.ws_handler.get_by_names(unique_ws_names)
    }
    results = {}
    valid_projects = []  # list of (key, workspace, project_name)
    for key in list_of_projects:
        parts = key.split("/")
        if len(parts) != 2:
            results[key] = {"error": 404}
            continue
        workspace = workspaces_by_name.get(parts[0])
        if not workspace:
            results[key] = {"error": 404}
            continue
        valid_projects.append((key, workspace, parts[1]))

    if valid_projects:
        # batch-fetch all requested projects, eagerly loading project_users so
        # members_by_role / get_role don't trigger per-project lazy loads
        ws_name_pairs = [(ws.id, name) for _, ws, name in valid_projects]
        found_projects = (
            projects_query(ProjectPermissions.Read, as_admin=False)
            .options(selectinload(Project.project_users))
            .filter(tuple_(Project.workspace_id, Project.name).in_(ws_name_pairs))
            .all()
        )
        found_map = {(p.workspace_id, p.name): p for p in found_projects}

        # batch-fetch all project members in one query
        users_map = {
            u.id: u.username
            for u in User.query.select_from(ProjectUser)
            .join(User)
            .filter(ProjectUser.project_id.in_([p.id for p in found_projects]))
            .all()
        }
        ws_ids = {p.workspace_id for p in found_projects}
        workspaces_map = {
            w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)
        }

        _precompute_has_conflict(found_projects)

        ctx = {"users_map": users_map, "workspaces_map": workspaces_map}

        for key, workspace, name in valid_projects:
            result = found_map.get((workspace.id, name))
            if result:
                results[key] = ProjectListSchema(context=ctx).dump(result)
            else:
                results[key] = (
                    {"error": 401}
                    if not current_user or not current_user.is_authenticated
                    else {"error": 404}
                )

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

    projects = (
        projects_query(ProjectPermissions.Read, as_admin=False)
        .options(selectinload(Project.project_users))
        .filter(Project.id.in_(proj_ids))
        .all()
    )
    _precompute_has_conflict(projects)
    ws_ids = set([p.workspace_id for p in projects])
    projects_ids = [p.id for p in projects]
    users_map = {
        u.id: u.username
        for u in User.query.select_from(ProjectUser)
        .join(User)
        .filter(ProjectUser.project_id.in_(projects_ids))
        .all()
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
    pagination = projects.options(selectinload(Project.project_users)).paginate(
        page=page, per_page=per_page
    )
    result = pagination.items
    total = pagination.total
    _precompute_has_conflict(result)

    # create user map id:username passed to project schema to minimize queries to db
    projects_ids = [p.id for p in result]
    users_map = {
        u.id: u.username
        for u in User.query.select_from(ProjectUser)
        .join(User)
        .filter(ProjectUser.project_id.in_(projects_ids))
        .all()
    }
    ws_ids = [p.workspace_id for p in result]
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
    parsed_access = parse_project_access_update_request(request.json.get("access", {}))

    # get current status for easier rollback
    modified_user_ids = []
    for role in list(ProjectRole.__reversed__()):
        modified_user_ids.extend(parsed_access.get(role, []))
    current_permissions_map = {
        user_id: project.get_role(user_id) for user_id in modified_user_ids
    }

    # get set of modified user_ids and possible (custom) errors
    id_diffs, error = current_app.ws_handler.update_project_members(
        project, parsed_access
    )

    # revert back rejected changes
    if error and hasattr(error, "rejected_emails"):
        rejected_users = (
            db.session.query(User.id)
            .filter(User.email.in_(error.rejected_emails))
            .all()
        )
        for user in rejected_users:
            if current_permissions_map[user.id] is None:
                project.unset_role(user.id)
            else:
                project.set_role(user.id, current_permissions_map[user.id])
        db.session.commit()

    if not id_diffs and error:
        # nothing was done but there are errors
        return jsonify(error.to_dict()), 422

    if "public" in request.json["access"]:
        project.public = request.json["access"]["public"]
        db.session.add(project)
        db.session.commit()

    # partial success
    if error:
        return jsonify(**error.to_dict(), project=ProjectSchema().dump(project)), 207
    return ProjectSchema().dump(project), 200


def catch_sync_failure(f):
    """Decorator to catch sync failures in push related endpoints"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            response, status_code = f(*args, **kwargs)
            if status_code >= 400:
                raise HTTPException(response=response)
            return response, status_code
        except IntegrityError:
            raise Conflict("Database integrity error")
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
            elif (
                request.endpoint
                == "/v2.mergin_sync_public_api_v2_controller_create_project_version"
            ):
                error_type = "project_push"

            description = (
                e.description if e.description else e.response.json.get("detail", "")
            )

            if project:
                project.sync_failed(
                    user_agent, error_type, str(description), current_user.id
                )
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
    version = ProjectVersion.from_v_name(request.json["version"])
    changes = request.json["changes"]
    project_permission = current_app.project_handler.get_push_permission(changes)
    project = require_project(namespace, project_name, project_permission)
    if project.locked_until:
        return ProjectLocked().response(422)
    # pass full project object to request for later use
    request.view_args["project"] = project
    ws = project.workspace
    if not ws:
        abort(404)

    # fixme use get_latest
    pv = ProjectVersion.query.filter_by(
        project_id=project.id, name=project.latest_version
    ).first()
    if pv and pv.name != version:
        abort(400, "Version mismatch")
    if not pv and version != 0:
        abort(400, "First push should be with v0")

    if all(len(changes[key]) == 0 for key in changes.keys()):
        abort(400, "No changes")

    try:
        ChangesSchema().validate(changes)
        upload_changes = ChangesSchema().dump(changes)
    except ValidationError as err:
        msg = err.messages[0] if type(err.messages) == list else "Invalid input data"
        abort(400, msg)

    for item in upload_changes["added"]:
        # check if same file is not already uploaded
        if not all(ele.path != item["path"] for ele in project.files):
            abort(400, f"File {item['path']} has been already uploaded")

    # Check user data limit
    updated_files = list(
        filter(
            lambda i: i.path in [f["path"] for f in upload_changes["updated"]],
            project.files,
        )
    )
    additional_disk_usage = (
        sum(
            file["size"] for file in upload_changes["added"] + upload_changes["updated"]
        )
        - sum(file.size for file in updated_files)
        - sum(file["size"] for file in upload_changes["removed"])
    )
    current_usage = ws.disk_usage()
    requested_storage = current_usage + additional_disk_usage
    if requested_storage > ws.storage:
        return StorageLimitHit(current_usage, ws.storage).response(422)

    try:
        upload = Upload.create_upload(
            project.id, version, upload_changes, current_user.id
        )
        if not upload:
            abort(400, "Another process is running. Please try later.")

        logging.info(
            f"Upload transaction {upload.transaction_id} created for project: {project.id}, version: {version}"
        )
    except (IntegrityError, SQLAlchemyError) as err:
        db.session.rollback()
        logging.exception(f"Failed to create upload: {str(err)}")
        abort(422, "Failed to create upload session. Please try later.")

    # Update immediately without uploading of new/modified files and remove transaction after successful commit
    if not (changes["added"] or changes["updated"]):
        next_version = version + 1
        file_changes = files_changes_from_upload(
            upload.changes, ProjectVersion.to_v_name(next_version)
        )
        user_agent = get_user_agent(request)
        device_id = get_device_id(request)
        try:
            pv = ProjectVersion(
                project,
                next_version,
                current_user.id,
                file_changes,
                get_ip(request),
                user_agent,
                device_id,
            )
            db.session.add(pv)
            db.session.add(project)
            db.session.commit()
            logging.info(
                f"A project version {ProjectVersion.to_v_name(next_version)} for project: {project.id} created. "
                f"Transaction id: {upload.transaction_id}. No upload."
            )
            project_version_created.send(pv)
            push_finished.send(pv)
            return jsonify(ProjectSchema().dump(project)), 200
        except IntegrityError as err:
            db.session.rollback()
            logging.exception(
                f"Failed to upload a new project version using transaction id: {upload.transaction_id}: {str(err)}"
            )
            abort(422, "Failed to upload a new project version. Please try later.")
        except gevent.timeout.Timeout:
            db.session.rollback()
            raise
        finally:
            upload.clear()

    return {"transaction": upload.transaction_id}, 200


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
    upload = get_upload_or_fail(transaction_id)
    request.view_args["project"] = upload.project
    chunks = []
    for file in upload.changes["added"] + upload.changes["updated"]:
        chunks += file.get("chunks", [])

    if chunk_id not in chunks:
        abort(404)

    dest = os.path.join(upload.upload_dir, "chunks", chunk_id)
    with upload.heartbeat(30):
        try:
            # we could have used request.data here, but it could eventually cause OOM issue
            save_to_file(request.stream, dest, current_app.config["MAX_CHUNK_SIZE"])
        except IOError:
            move_to_tmp(dest, transaction_id)
            abort(400, "Too big chunk")
        if os.path.exists(dest):
            checksum = generate_checksum(dest)
            size = os.path.getsize(dest)
            return jsonify({"checksum": checksum, "size": size}), 200
        else:
            abort(400, "Upload was probably canceled")


@auth_required
@catch_sync_failure
def push_finish(transaction_id):
    """Finalize project data upload.

    Steps involved in finalization:
     - merge chunks together (if there are some)
     - do integrity check comparing uploaded file sizes with what was expected
     - move uploaded files to new version dir and applying sync changes (e.g. geodiff apply_changeset)
     - bump up version in database
     - remove artifacts (chunks) by moving them to tmp directory

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    upload = get_upload_or_fail(transaction_id)
    request.view_args["project"] = upload.project
    project = upload.project
    next_version = project.next_version()
    v_next_version = ProjectVersion.to_v_name(next_version)
    version_dir = os.path.join(project.storage.project_dir, v_next_version)
    if project.locked_until:
        return ProjectLocked().response(422)

    file_changes, errors = upload.process_chunks(use_shared_chunk_dir=False)
    if errors:
        upload.clear()

        unsupported_files = [
            k for k, v in errors.items() if v == FileSyncErrorType.UNSUPPORTED.value
        ]
        if len(unsupported_files):
            abort(
                400,
                f"Unsupported file type detected: '{unsupported_files[0]}'. "
                f"Please remove the file or try compressing it into a ZIP file before uploading.",
            )

        corrupted_files = [
            k for k, v in errors.items() if v == FileSyncErrorType.CORRUPTED.value
        ]
        if corrupted_files:
            abort(422, {"corrupted_files": corrupted_files})

        sync_errors = {
            k: v for k, v in errors.items() if FileSyncErrorType.SYNC_ERROR.value in v
        }
        if sync_errors:
            msg = ""
            for key, value in sync_errors.items():
                msg += key + " error=" + value + "\n"

            abort(422, f"Failed to create new version: {msg}")

    files_dir = os.path.join(upload.upload_dir, "files", v_next_version)
    target_dir = os.path.join(project.storage.project_dir, v_next_version)
    if os.path.exists(target_dir):
        pv = ProjectVersion.query.filter_by(
            project_id=project.id, name=project.latest_version
        ).first()
        if pv and pv.name == upload.version + 1:
            abort(
                409,
                f"There is already version with this name {v_next_version}",
            )
        logging.info(
            "Upload transaction: Target directory already exists. Overwriting %s"
            % target_dir
        )
        move_to_tmp(target_dir)

    try:
        # let's keep upload alive until all work is done so no one else can claim it
        with upload.heartbeat(5):
            user_agent = get_user_agent(request)
            device_id = get_device_id(request)
            pv = ProjectVersion(
                project,
                next_version,
                current_user.id,
                file_changes,
                get_ip(request),
                user_agent,
                device_id,
            )
            db.session.add(pv)
            db.session.add(project)

            # move files before committing so a filesystem failure leaves the DB clean
            if os.path.exists(files_dir):
                os.renames(files_dir, version_dir)

            db.session.commit()

            logging.info(
                f"Push finished for project: {project.id}, project version: {v_next_version}, transaction id: {transaction_id}."
            )
            project_version_created.send(pv)
            push_finished.send(pv)
    except (psycopg2.Error, OSError, IntegrityError) as err:
        db.session.rollback()
        logging.exception(
            f"Failed to finish push for project: {project.id}, project version: {v_next_version}, "
            f"transaction id: {transaction_id}.: {str(err)}"
        )
        if (
            os.path.exists(version_dir)
            and not ProjectVersion.query.filter_by(
                project_id=project.id, name=next_version
            ).count()
        ):
            move_to_tmp(version_dir)
        abort(422, "Failed to create new version: {}".format(str(err)))
    # catch exception during pg transaction so we can rollback and prevent PendingRollbackError during upload clean up
    except gevent.timeout.Timeout:
        db.session.rollback()
        if (
            os.path.exists(version_dir)
            and not ProjectVersion.query.filter_by(
                project_id=project.id, name=next_version
            ).count()
        ):
            move_to_tmp(version_dir)
        raise
    finally:
        # remove artifacts
        upload.clear()

    return jsonify(ProjectSchema().dump(project)), 200


@auth_required
def push_cancel(transaction_id):
    """Cancel upload transaction

    Cancel ongoing upload. Uploaded files are removed and another upload can be started. # noqa: E501

    :param transaction_id: Transaction id.
    :type transaction_id: str

    :rtype: None
    """
    upload = get_upload_or_fail(transaction_id)
    upload.clear()
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
    if not dest_project:
        abort(400, "Project name cannot be empty")
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
    validation = project_name_validation(dest_project)
    if validation and dest_project != cloned_project.name:
        abort(400, validation)

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

    # Check storage limit
    additional_storage = cloned_project.disk_usage
    current_usage = ws.disk_usage()
    requested_storage = current_usage + additional_storage
    if requested_storage > ws.storage:
        abort(
            make_response(
                jsonify(StorageLimitHit(current_usage, ws.storage).to_dict()), 422
            )
        )

    p = Project(
        name=dest_project,
        storage_params={"type": "local", "location": generate_location()},
        creator=current_user,
        workspace=ws,
    )
    p.updated = datetime.utcnow()
    db.session.add(p)
    files_to_exclude = current_app.config.get("EXCLUDED_CLONE_FILENAMES", [])

    try:
        p.storage.initialize(
            template_project=cloned_project, excluded_files=files_to_exclude
        )
    except InitializationError as e:
        abort(400, f"Failed to clone project: {str(e)}")

    version = 1 if cloned_project.files else 0
    # TODO: add user_agent and device_id handling to class
    user_agent = get_user_agent(request)
    device_id = get_device_id(request)
    # transform source files to new uploaded files
    file_changes = []
    for file in cloned_project.files:
        if os.path.basename(file.path) in files_to_exclude:
            continue
        file_changes.append(
            ProjectFileChange(
                file.path,
                file.checksum,
                file.size,
                diff=None,
                mtime=None,
                location=os.path.join("v1", mergin_secure_filename(file.path)),
                change=PushChangeType.CREATE,
            )
        )
    project_version = ProjectVersion(
        p,
        version,
        current_user.id,
        file_changes,
        get_ip(request),
        user_agent,
        device_id,
    )
    db.session.add(project_version)
    db.session.commit()
    project_version_created.send(project_version)
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
    fh = (
        FileHistory.query.join(ProjectFilePath)
        .join(FileHistory.version)
        .filter(
            ProjectVersion.project_id == project.id,
            ProjectFilePath.path == path,
            FileHistory.change != "delete",
        )
        .order_by(desc(ProjectVersion.created))
        .first_or_404(f"File {path} not found")
    )

    data = ProjectFileSchema().dump(fh)
    history = FileHistory.changes(project.id, path, 1, project.latest_version)

    # batch-load all rank-0 FileDiff records needed for the history in one query
    diff_map = {}
    if history:
        update_diff_versions = [
            i.project_version_name
            for i in history
            if i.change == PushChangeType.UPDATE_DIFF.value
        ]
        if update_diff_versions:
            diffs = FileDiff.query.filter(
                FileDiff.file_path_id == history[0].file_path_id,
                FileDiff.rank == 0,
                FileDiff.version.in_(update_diff_versions),
            ).all()
            diff_map = {d.version: d for d in diffs}

    history_field = {}
    for item in history:
        if item.change == PushChangeType.UPDATE_DIFF.value:
            item.__dict__["diff"] = diff_map.get(item.project_version_name)
        history_field[ProjectVersion.to_v_name(item.version.name)] = FileHistorySchema(
            exclude=("mtime", "expiration")
        ).dump(item)

    data["history"] = history_field
    return data, 200


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
        project_id=project.id, name=ProjectVersion.from_v_name(version_id)
    ).first()
    if not version:
        abort(
            404, f"Version {version_id} in project {namespace}/{project_name} not found"
        )

    # FIXME optimize, do a lookup in database
    file = next(
        (f for f in version.files if f.location == os.path.join(version_id, path)),
        None,
    )
    if not file:
        abort(404, f"File {path} not found")

    if not file.diff:
        abort(404, "Diff not found")

    changeset = os.path.join(version.project.storage.project_dir, file.diff.location)
    json_file = os.path.join(
        version.project.storage.project_dir, file.location + "-diff-changeset"
    )
    basefile = os.path.join(version.project.storage.project_dir, file.location)
    schema_file = os.path.join(
        version.project.storage.project_dir, file.location + "-schema"
    )
    project.storage.flush_geodiff_logger()  # clean geodiff logger

    try:
        if not os.path.exists(basefile):
            version.project.storage.restore_versioned_file(
                path, ProjectVersion.from_v_name(version_id)
            )
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
                wkb = version.project.storage.geodiff.create_wkb_from_gpkg_header(
                    gpkg_wkb
                )
                wkt = wkb2wkt(wkb)
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
        or ws.get_user_role(current_user) == WorkspaceRole.GUEST
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
        project_id=project.id, name=ProjectVersion.from_v_name(version)
    ).first_or_404()
    data = ProjectVersionSchema(exclude=["files"]).dump(pv)
    return data, 200
