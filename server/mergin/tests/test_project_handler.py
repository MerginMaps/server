from ..sync.project_handler import GlobalProjectHandler
from ..sync.permissions import ProjectPermissions

def test_project_handler():
    project_handler = GlobalProjectHandler()
    project_permission = project_handler.get_push_permission(None)
    assert project_permission == ProjectPermissions.Upload
