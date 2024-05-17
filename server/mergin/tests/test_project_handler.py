from ..sync.project_handler import ProjectHandler
from ..sync.permissions import ProjectPermissions


def test_project_handler():
    project_handler = ProjectHandler()
    project_permission = project_handler.get_push_permission(None)
    assert project_permission == ProjectPermissions.Upload
