# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional, Set, List
from flask_login import current_user
from sqlalchemy import Column, literal, extract
from sqlalchemy.sql.operators import is_

from .errors import UpdateProjectAccessError
from .models import (
    Project,
    AccessRequest,
    ProjectAccessDetail,
    ProjectRole,
    ProjectVersion,
    ProjectUser,
)
from .permissions import projects_query, ProjectPermissions
from ..app import db
from ..auth.models import User
from ..config import Configuration
from .interfaces import AbstractWorkspace, WorkspaceHandler, WorkspaceRole


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
        if role is WorkspaceRole.OWNER:
            return True

        if permissions == "read":
            return role >= WorkspaceRole.READER
        elif permissions == "edit":
            return role >= WorkspaceRole.EDITOR
        elif permissions == "write":
            return role >= WorkspaceRole.WRITER
        elif permissions == "admin":
            return role >= WorkspaceRole.ADMIN
        else:
            return False

    def user_is_member(self, user):
        return True

    def get_user_role(self, user) -> WorkspaceRole:
        if user.is_admin:
            return WorkspaceRole.OWNER
        if Configuration.GLOBAL_ADMIN:
            return WorkspaceRole.ADMIN
        if Configuration.GLOBAL_WRITE:
            return WorkspaceRole.WRITER
        if Configuration.GLOBAL_READ:
            return WorkspaceRole.READER
        return WorkspaceRole.GUEST

    def project_count(self):
        from .models import Project

        return (
            db.session.query(Project.disk_usage)
            .filter(Project.workspace_id == self.id)
            .filter(Project.removed_at.is_(None))
            .count()
        )

    def members(self):
        return [
            (user, self.get_user_role(user))
            for user in User.query.filter(User.active.is_(True))
            .order_by(User.email)
            .all()
        ]

    def can_add_users(self, user: User) -> bool:
        return user.is_admin


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
                Project.query.filter(Project.storage_params.isnot(None))
                .filter(Project.removed_at.is_(None))
                .filter(Project.public.is_(True))
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
                    projects = projects.filter(Project.creator_id != user.id)
                    # check global read permissions or direct project permissions
                    if workspace.user_has_permissions(user, "read"):
                        projects = projects.filter(Project.workspace_id == workspace.id)
                    else:
                        subquery = (
                            db.session.query(ProjectUser.project_id)
                            .filter(ProjectUser.user_id == user.id)
                            .subquery()
                        )
                        projects = projects.filter(Project.id.in_(subquery))

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

    @staticmethod
    def monthly_contributors_count(month_offset=0):
        today = datetime.now(timezone.utc)
        year = today.year
        month = today.month
        return (
            db.session.query(ProjectVersion.author_id)
            .filter(
                extract("year", ProjectVersion.created) == year,
                extract("month", ProjectVersion.created) == month - month_offset,
            )
            .group_by(ProjectVersion.author_id)
            .count()
        )

    def projects_query(self, like: str = None):
        ws = self.factory_method()
        query = db.session.query(
            Project,
            literal(ws.name).label("workspace_name"),
        ).filter(Project.storage_params.isnot(None))

        if like:
            query = query.filter(
                Project.name.ilike(f"%{like}%") | literal(ws.name).ilike(f"%{like}%")
            )
        return query

    @staticmethod
    def update_project_members(
        project: Project, access: Dict
    ) -> Tuple[Set[int], Optional[UpdateProjectAccessError]]:
        """Update project members doing bulk access update"""
        error = None
        id_diffs = project.bulk_roles_update(access)
        db.session.add(project)
        db.session.commit()

        if access.get("invalid_usernames") or access.get("invalid_ids"):
            error = UpdateProjectAccessError(
                access["invalid_usernames"], access["invalid_ids"]
            )
        return id_diffs, error

    @staticmethod
    def access_requests_query():
        """Project access base query"""
        return AccessRequest.query.join(Project)

    def project_access(self, project: Project) -> List[ProjectAccessDetail]:
        """
        Project access users overview
        """
        ws = self.factory_method()
        result = []
        global_role = None
        if Configuration.GLOBAL_ADMIN:
            global_role = "owner"
        elif Configuration.GLOBAL_WRITE:
            global_role = "writer"
        elif Configuration.GLOBAL_READ:
            global_role = "reader"

        direct_members_ids = [u.user_id for u in project.project_users]
        users = User.query.filter(User.active.is_(True)).order_by(User.email)
        direct_members = users.filter(User.id.in_(direct_members_ids)).all()

        for dm in direct_members:
            project_role = ProjectPermissions.get_user_project_role(project, dm)
            member = ProjectAccessDetail(
                id=dm.id,
                username=dm.username,
                role=ws.get_user_role(dm).value,
                name=dm.profile.name(),
                email=dm.email,
                project_permission=project_role and project_role.value,
                type="member",
            )
            result.append(member)
        if global_role:
            global_members = users.filter(User.id.notin_(direct_members_ids)).all()
            for gm in global_members:
                member = ProjectAccessDetail(
                    id=gm.id,
                    username=gm.username,
                    name=gm.profile.name(),
                    email=gm.email,
                    role=global_role,
                    project_permission=global_role,
                    type="member",
                )
                result.append(member)
        return result

    def server_editors_count(self) -> int:
        if Configuration.GLOBAL_ADMIN or Configuration.GLOBAL_WRITE:
            return User.query.filter(
                is_(User.username.ilike("deleted_%"), False) | User.active
            ).count()
        if Configuration.GLOBAL_READ:
            return User.query.filter(
                is_(User.username.ilike("deleted_%"), False) | User.active,
                User.is_admin.is_(True),
            ).count()

        return (
            db.session.query(ProjectUser.user_id)
            .select_from(Project)
            .join(ProjectUser)
            .filter(
                Project.removed_at.is_(None),
                ProjectUser.role != ProjectRole.READER.value,
            )
            .group_by(ProjectUser.user_id)
            .count()
        )
