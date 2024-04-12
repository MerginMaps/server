// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { DropdownOption } from './components/types'

import { ProjectAccess } from '@/modules'

export enum UserRole {
  guest,
  reader,
  writer,
  admin,
  owner
}

export enum ProjectRole {
  none,
  reader,
  writer,
  owner
}

export enum GlobalRole {
  global_read,
  global_write,
  global_admin
}

export type UserRoleName = 'guest' | 'reader' | 'writer' | 'admin' | 'owner'

export type ProjectRoleName =
  | Extract<UserRoleName, 'reader' | 'writer' | 'owner'>
  | 'none'

export type ProjectPermissionName = 'owner' | 'write' | 'read'

export const USER_ROLE_NAME_BY_ROLE: Record<UserRole, UserRoleName> = {
  [UserRole.guest]: 'guest',
  [UserRole.reader]: 'reader',
  [UserRole.writer]: 'writer',
  [UserRole.admin]: 'admin',
  [UserRole.owner]: 'owner'
}

export const USER_ROLE_BY_NAME: Record<UserRoleName, UserRole> = {
  guest: UserRole.guest,
  reader: UserRole.reader,
  writer: UserRole.writer,
  admin: UserRole.admin,
  owner: UserRole.owner
}

export const PROJECT_ROLE_NAME_BY_ROLE: Record<ProjectRole, ProjectRoleName> = {
  [ProjectRole.none]: 'none',
  [ProjectRole.reader]: 'reader',
  [ProjectRole.writer]: 'writer',
  [ProjectRole.owner]: 'owner'
}

export const PROJECT_ROLE_BY_NAME: Record<ProjectRoleName, ProjectRole> = {
  none: ProjectRole.none,
  reader: ProjectRole.reader,
  writer: ProjectRole.writer,
  owner: ProjectRole.owner
}

export enum ProjectPermission {
  read,
  write,
  owner
}

export const PROJECT_PERMISSION_NAME_BY_PERMISSION: Record<
  ProjectPermission,
  ProjectPermissionName
> = {
  [ProjectPermission.read]: 'read',
  [ProjectPermission.write]: 'write',
  [ProjectPermission.owner]: 'owner'
}

export const PROJECT_PERMISSION_BY_NAME: Record<
  ProjectPermissionName,
  ProjectPermission
> = {
  read: ProjectPermission.read,
  write: ProjectPermission.write,
  owner: ProjectPermission.owner
}

export function isAtLeastRole(roleName: UserRoleName, role: UserRole): boolean {
  return USER_ROLE_BY_NAME[roleName] >= role
}

export function isAtLeastProjectRole(
  roleName: ProjectRoleName,
  role: ProjectRole
): boolean {
  return PROJECT_ROLE_BY_NAME[roleName] >= role
}

export function isAtLeastProjectPermission(
  permissionName: ProjectPermissionName,
  permission: ProjectPermission
): boolean {
  return PROJECT_PERMISSION_BY_NAME[permissionName] >= permission
}

export function isAtLeastGlobalRole(
  roleName: ProjectRoleName,
  globalRole: GlobalRole
): boolean {
  // We have also none role, so we need to add 1 to the global role
  return PROJECT_ROLE_BY_NAME[roleName] >= globalRole + 1
}

export function getProjectRoleNameValues(): DropdownOption<ProjectRoleName>[] {
  return [
    {
      value: 'reader',
      label: 'Reader',
      description: 'Can view project files',
      disabled: true
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
    reader: 'readersnames',
    none: undefined
  }
  return mapper[roleName]
}

export function getProjectPermissionByRoleName(
  roleName: ProjectRoleName
): ProjectPermissionName {
  const mapper: Record<ProjectRoleName, ProjectPermissionName | undefined> = {
    owner: 'owner',
    writer: 'write',
    reader: 'read',
    none: undefined
  }
  return mapper[roleName]
}
