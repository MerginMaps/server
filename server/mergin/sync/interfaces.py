# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from abc import ABC, abstractmethod


class AbstractWorkspace:
    """
    Defines both the abstraction and the interface for the workspace object.
    This abstract object should be used everywhere in the client code (e.g. sync module).
    Correct implementation to be passed is ensured by WorkpaceHandler.
    """

    @property
    @abstractmethod
    def id(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @name.setter
    def name(self, value):
        pass

    @property
    @abstractmethod
    def storage(self):
        pass

    @storage.setter
    def storage(self, value):
        pass

    @property
    @abstractmethod
    def is_active(self):
        pass

    @is_active.setter
    def is_active(self, value):
        pass

    @abstractmethod
    def disk_usage(self):
        """Space occupied by all projects in workspace in bytes"""
        pass

    def user_has_permissions(self, user, permissions):
        """Check whether User obj has read/write/admin permissions to workspace
        Current rules are:
        - read: user can list and download all projects within workspace
        - write: user can push to any projects within workspace
        - admin: user can create new projects, delete projects within workspace
        and modify read/write permissions for other users
        """
        pass

    def user_is_member(self, user):
        """Check if user is workspace member regardless of role/permissions"""
        pass

    @abstractmethod
    def get_user_role(self, user):
        """Get user role in workspace"""
        pass

    @abstractmethod
    def project_count(self):
        """Return number of workspace projects"""
        pass


class WorkspaceHandler(ABC):
    """
    Declares interface for the factory method and other useful methods like filters which should return
    either single or a list of Workspace objects.
    """

    @abstractmethod
    def factory_method(self, *arg):
        pass

    @abstractmethod
    def get(self, id_):
        """
        Return workspace of required id
        """
        pass

    @abstractmethod
    def get_by_name(self, name):
        """
        Return workspace of required name
        """
        pass

    @abstractmethod
    def get_by_project(self, project):
        """
        Return workspace of required project
        """
        pass

    @abstractmethod
    def get_by_ids(self, ids):
        """
        Return list of workspace with ids present in the given list
        """
        pass

    @abstractmethod
    def list_user_workspaces(self, name, active=False):
        """
        Return list of workspace where user has any access, optionally filtered out to active workspace only
        """
        pass

    @abstractmethod
    def list_active(self):
        """
        Return list of workspace which are active
        """
        pass

    @abstractmethod
    def list_all(self):
        """
        Return list of all workspaces
        """
        pass

    @abstractmethod
    def get_preferred(self, user):
        """
        Return preferred workspace for user as a hint for clients
        """
        pass

    def list_user_invitations(self, user):
        """
        Return list of workspace active invitations for user
        """
        pass

    @staticmethod
    def workspace_count():
        """
        Return number of workspaces
        """
        pass
