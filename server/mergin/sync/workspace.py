# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Set, List
from flask_login import current_user
from sqlalchemy import or_, and_, Column, literal
from sqlalchemy.orm import joinedload

from .errors import UpdateProjectAccessError
from .models import Project, ProjectAccess, AccessRequest, ProjectAccessDetail
from .permissions import projects_query, ProjectPermissions, get_user_project_role
from .public_api_controller import parse_project_access_update_request
from .. import db
from ..auth.models import User
from ..config import Configuration
from .interfaces import AbstractWorkspace, WorkspaceHandler


class GlobalWorkspace(AbstractWorkspace):
    """Implements single workspace based on global settings"""

    def __init__(self):
        self.name = Configuration.GLOBAL_WORKSPACE
        self.storage = Configuration.GLOBAL_STORAGE
        self.id = 1

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    @property
    def is_active(self):
        return True

    def disk_usage(self):
        # get only what is necessary from db to calculate final usage
        from .models import Project

        projects_usage_list = (
            db.session.query(Project.disk_usage)
            .filter(Project.removed_at.is_(None))
            .all()
        )
        return sum(p.disk_usage for p in projects_usage_list)

    def user_has_permissions(self, user, permissions):
        role = self.get_user_role(user)
        # mergin super-user has all permissions
        if role == "owner":
            return True

        if permissions == "read":
            return role in ["admin", "writer", "reader"]
        elif permissions == "write":
            return role in ["admin", "writer"]
        elif permissions == "admin":
            return role == "admin"
        else:
            return False

    def user_is_member(self, user):
        return True

    def get_user_role(self, user):
        if user.is_admin:
            return "owner"
        if Configuration.GLOBAL_ADMIN:
            return "admin"
        if Configuration.GLOBAL_WRITE:
            return "writer"
        if Configuration.GLOBAL_READ:
            return "reader"
        return "guest"

    def project_count(self):
        from .models import Project

        return (
            db.session.query(Project.disk_usage)
            .filter(Project.workspace_id == self.id)
            .filter(Project.removed_at.is_(None))
            .count()
        )


class GlobalWorkspaceHandler(WorkspaceHandler):
    """Implements handler for GlobalWorkspace objects"""

    def factory_method(self):
        return GlobalWorkspace()

    def get(self, id_):
        if GlobalWorkspace().id == id_:
            return self.factory_method()

    def get_by_name(self, name):
        if name != Configuration.GLOBAL_WORKSPACE:
            return
        return self.factory_method()

    def get_by_project(self, project):
        return self.factory_method()

    def get_by_ids(self, ids):
        return [self.factory_method()]

    def list_active(self):
        return [self.factory_method()]

    def list_user_workspaces(self, name, active=False):
        return [self.factory_method()]

    def list_all(self):
        return [self.factory_method()]

    def get_preferred(self, user):
        return self.factory_method()

    def list_user_invitations(self, user):
        return []

    def filter_projects(
        self,
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
    ):
        if only_public:
            projects = (
                Project.query.filter(Project.access.has(public=only_public))
                .filter(Project.storage_params.isnot(None))
                .filter(Project.removed_at.is_(None))
            )
        else:
            projects = projects_query(
                ProjectPermissions.Read, as_admin=as_admin, public=public
            )

        workspace = self.factory_method()
        if flag:
            user = User.query.filter_by(username=user).first() if user else current_user
            if user and not user.is_anonymous and user.active:
                if flag == "created":
                    projects = projects.filter(Project.creator_id == user.id)
                if flag == "shared":
                    # check global read permissions
                    if workspace.user_has_permissions(user, "read"):
                        read_access_workspace_id = workspace.id
                    else:
                        read_access_workspace_id = None
                    projects = projects.filter(
                        or_(
                            and_(
                                Project.access.has(
                                    ProjectAccess.readers.contains([user.id])
                                ),
                                Project.creator_id != user.id,
                            ),
                            and_(
                                Project.workspace_id == read_access_workspace_id,
                                Project.creator_id != user.id,
                            ),
                        )
                    )

        if name:
            projects = projects.filter(Project.name.ilike("%{}%".format(name)))

        # legacy option, it either matches global workspace or not
        if namespace and namespace != workspace.name:
            projects = projects.filter(Project.workspace_id != workspace.id)

        # legacy option, it either matches global workspace or not
        if only_namespace and only_namespace != workspace.name:
            projects = projects.filter(Project.workspace_id != workspace.id)

        if last_updated_in:
            projects = projects.filter(
                Project.updated >= datetime.utcnow() - timedelta(days=last_updated_in)
            )

        projects = projects.options(joinedload(Project.access))

        if order_params:
            order_by_params = []
            for p in order_params.split(","):
                string_param = p.strip()
                if "_asc" in string_param:
                    ascending = True
                    string_param = string_param.replace("_asc", "")
                else:
                    ascending = False
                    string_param = string_param.replace("_desc", "")

                if string_param in ["workspace", "namespace"]:
                    continue  # legacy sort by namespace name
                else:
                    attr = string_param

                order_attr = Project.__table__.c.get(attr, None)
                # make sure attribute is a valid table column
                if not isinstance(order_attr, Column):
                    continue

                order_attr = order_attr.asc() if ascending else order_attr.desc()
                order_by_params.append(order_attr)
            projects = projects.order_by(*order_by_params)
        elif order_by and order_by != "namespace":
            # ensure backward compatibility for clients using old api
            order_attr = Project.__table__.c.get(order_by, None)
            # make sure attribute is a valid table column
            if isinstance(order_attr, Column):
                order_attr = order_attr.desc() if descending else order_attr.asc()
                projects = projects.order_by(order_attr)
        return projects

    @staticmethod
    def workspace_count():
        return 1

    def projects_query(self, name=None, workspace=None):
        ws = self.factory_method()
        query = db.session.query(
            Project, literal(ws.name).label("workspace_name")
        ).filter(Project.storage_params.isnot(None))

        if name:
            query = query.filter(Project.name.ilike(f"%{name}%"))
        if workspace:
            query = query.filter(literal(ws.name).ilike(f"%{workspace}%"))
        return query

    @staticmethod
    def update_project_members(
        project: Project, access: Dict
    ) -> Tuple[Set[int], Optional[UpdateProjectAccessError]]:
        """Update project members doing bulk access update"""
        error = None
        parsed_access = parse_project_access_update_request(access)
        id_diffs = project.access.bulk_update(parsed_access)
        db.session.add(project)
        db.session.commit()
        if parsed_access.get("invalid_usernames") or parsed_access.get("invalid_ids"):
            error = UpdateProjectAccessError(
                parsed_access["invalid_usernames"], parsed_access["invalid_ids"]
            )
        return id_diffs, error

    @staticmethod
    def access_requests_query():
        """Project access base query"""
        return AccessRequest.query.join(Project)

    def project_access(self, project: Project):
        """
        Project access users overview
        """
        ws = self.factory_method()
        if (
            Configuration.GLOBAL_ADMIN
            or Configuration.GLOBAL_WRITE
            or Configuration.GLOBAL_READ
        ):
            members = User.query.filter(User.active.is_(True)).all()
        else:
            member_ids = set(
                project.access.readers + project.access.writers + project.access.owners
            )
            members = User.query.filter(User.active, User.id.in_(member_ids)).all()
        result = []
        for member in members:
            result.append(
                ProjectAccessDetail(
                    id=member.id,
                    type="member",
                    username=member.username,
                    workspace_role=ws.get_user_role(member),
                    name=member.profile.name(),
                    email=member.email,
                    project_permission=get_user_project_role(project, member),
                ).to_dict()
            )
        return result
