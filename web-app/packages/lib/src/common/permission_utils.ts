// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { DropdownOption } from './components/types'

import { ProjectAccess } from '@/modules'

export enum WorkspaceRole {
  guest,
  reader,
  editor,
  writer,
  admin,
  owner
}

export enum ProjectRole {
  reader,
  editor,
  writer,
  owner
}

export enum GlobalRole {
  global_read,
  global_write,
  global_admin
}

export enum ProjectPermission {
  read,
  edit,
  write,
  owner
}

export type WorkspaceRoleName = keyof typeof WorkspaceRole

export type ProjectRoleName = keyof typeof ProjectRole

export type ProjectPermissionName = keyof typeof ProjectPermission

export const USER_ROLE_NAME_BY_ROLE: Record<WorkspaceRole, WorkspaceRoleName> =
  {
    [WorkspaceRole.guest]: 'guest',
    [WorkspaceRole.reader]: 'reader',
    [WorkspaceRole.editor]: 'editor',
    [WorkspaceRole.writer]: 'writer',
    [WorkspaceRole.admin]: 'admin',
    [WorkspaceRole.owner]: 'owner'
  }

export const PROJECT_ROLE_NAME_BY_ROLE: Record<ProjectRole, ProjectRoleName> = {
  [ProjectRole.reader]: 'reader',
  [ProjectRole.editor]: 'editor',
  [ProjectRole.writer]: 'writer',
  [ProjectRole.owner]: 'owner'
}


export function isAtLeastRole(
  roleName: WorkspaceRoleName,
  role: WorkspaceRole
): boolean {
  return WorkspaceRole[roleName] >= role
}

export function isAtLeastProjectRole(
  roleName: ProjectRoleName,
  role: ProjectRole
): boolean {
  return ProjectRole[roleName] >= role
}

export function isAtLeastProjectPermission(
  permissionName: ProjectPermissionName,
  permission: ProjectPermission
): boolean {
  return ProjectPermission[permissionName] >= permission
}

export function isAtLeastGlobalRole(
  roleName: ProjectRoleName,
  globalRole: GlobalRole
): boolean {
  const globalProjectRole = {
    [GlobalRole.global_read]: ProjectRole.reader,
    [GlobalRole.global_write]: ProjectRole.writer,
    [GlobalRole.global_admin]: ProjectRole.owner
  }
  return ProjectRole[roleName] >= globalProjectRole[globalRole]
}

export function getProjectRoleNameValues(): DropdownOption<ProjectRoleName>[] {
  return [
    {
      value: 'reader',
      label: 'Reader',
      description: 'Can view project files'
    },
    {
      value: 'editor',
      label: 'Editor',
      description: 'Can collect features in project'
    },
    {
      value: 'writer',
      label: 'Writer',
      description: 'Can edit project files'
    },
    {
      value: 'owner',
      label: 'Owner',
      description: 'Can share and remove project'
    }
  ]
}

export function getProjectPermissionsValues(): DropdownOption<ProjectPermissionName>[] {
  return [
    {
      value: 'read',
      label: 'Reader',
      description: 'Can view project files'
    },
    {
      value: 'edit',
      label: 'Editor',
      description: 'Can collect features in project'
    },
    {
      value: 'write',
      label: 'Writer',
      description: 'Can edit project files'
    },
    {
      value: 'owner',
      label: 'Owner',
      description: 'Can share and remove project'
    }
  ]
}

export function getProjectAccessKeyByRoleName(
  roleName: ProjectRoleName
): keyof ProjectAccess {
  const mapper: Record<ProjectRoleName, keyof ProjectAccess | undefined> = {
    owner: 'ownersnames',
    writer: 'writersnames',
    editor: 'editorsnames',
    reader: 'readersnames'
  }
  return mapper[roleName]
}

export function getProjectPermissionByRoleName(
  roleName: ProjectRoleName
): ProjectPermissionName {
  const mapper: Record<ProjectRoleName, ProjectPermissionName> = {
    owner: 'owner',
    writer: 'write',
    editor: 'edit',
    reader: 'read'
  }
  return mapper[roleName]
}
