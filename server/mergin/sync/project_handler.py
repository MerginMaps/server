from .interfaces import ProjectHandler
from .permissions import ProjectPermissions


class GlobalProjectHandler(ProjectHandler):
    def get_push_permission(self, changes: dict):
        return ProjectPermissions.Upload
