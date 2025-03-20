from .models import ProjectRole, ProjectUser
from .interfaces import AbstractProjectHandler
from .permissions import ProjectPermissions
from sqlalchemy import or_, and_
from typing import List
from ..auth.models import User, UserProfile


class ProjectHandler(AbstractProjectHandler):
    def get_push_permission(self, changes: dict):
        return ProjectPermissions.Upload

    def get_email_receivers(self, project_id: str) -> List[User]:
        return (
            User.query.join(UserProfile)
            .outerjoin(ProjectUser, ProjectUser.user_id == User.id)
            .filter(
                or_(
                    and_(
                        ProjectUser.project_id == project_id,
                        ProjectUser.role == ProjectRole.OWNER.value,
                    ),
                    User.is_admin,
                ),
                User.verified_email,
                UserProfile.receive_notifications,
            )
            .all()
        )
