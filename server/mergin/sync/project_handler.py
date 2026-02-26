from .models import ProjectRole, ProjectUser, Project
from .interfaces import AbstractProjectHandler
from .permissions import ProjectPermissions
from sqlalchemy import or_, and_
from typing import List
from ..auth.models import User, UserProfile


class ProjectHandler(AbstractProjectHandler):
    def get_push_permission(self, changes: dict):
        return ProjectPermissions.Upload

    def get_email_receivers(self, project: Project) -> List[User]:
        return (
            User.query.join(UserProfile)
            .outerjoin(ProjectUser, ProjectUser.user_id == User.id)
            .filter(
                or_(
                    and_(
                        ProjectUser.project_id == project.id,
                        ProjectUser.role == ProjectRole.OWNER.value,
                    ),
                    User.is_admin,
                ),
                User.active,
                User.verified_email,
                UserProfile.receive_notifications,
            )
            .all()
        )

    @staticmethod
    def get_projects_by_uuids(uuids: List[str]) -> [Project]:
        """Gets non-deleted projects"""
        return (
            Project.query.filter(Project.id.in_(uuids))
            .filter(Project.storage_params.isnot(None))
            .filter(Project.removed_at.is_(None))
            .all()
        )
