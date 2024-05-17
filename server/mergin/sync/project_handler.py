from .interfaces import AbstractProjectHandler
from .permissions import ProjectPermissions


class ProjectHandler(AbstractProjectHandler):
    def get_push_permission(self, changes: dict):
        return ProjectPermissions.Upload
