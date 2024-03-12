// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

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

export type UserRoleName = 'guest' | 'reader' | 'writer' | 'admin' | 'owner'

export type ProjectRoleName =
  | Extract<UserRoleName, 'reader' | 'writer' | 'owner'>
  | 'none'

export const USER_ROLE_NAME_BY_ROLE: Record<UserRole, UserRoleName> = {
  [UserRole.guest]: 'guest',
  [UserRole.reader]: 'reader',
  [UserRole.writer]: 'writer',
  [UserRole.admin]: 'admin',
  [UserRole.owner]: 'owner'
}

export const USER_ROLE_LABEL_BY_NAME: Record<UserRoleName, string> = {
  guest: 'Guest',
  reader: 'Reader',
  writer: 'Writer',
  admin: 'Admin',
  owner: 'Owner'
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

export const PROJECT_ROLE_LABEL_BY_NAME: Record<ProjectRoleName, string> = {
  none: 'None',
  reader: 'Reader',
  writer: 'Writer',
  owner: 'Owner'
}

export const PROJECT_ROLE_BY_NAME: Record<ProjectRoleName, ProjectRole> = {
  none: ProjectRole.none,
  reader: ProjectRole.reader,
  writer: ProjectRole.writer,
  owner: ProjectRole.owner
}

export interface UserRoleValueForSelect {
  label: string
  value: UserRoleName
}

export enum ProjectPermission {
  read,
  write,
  owner
}

export type ProjectPermissionName = 'owner' | 'write' | 'read'

export const PROJECT_PERMISSION_NAME_BY_PERMISSION: Record<
  ProjectPermission,
  ProjectPermissionName
> = {
  [ProjectPermission.read]: 'read',
  [ProjectPermission.write]: 'write',
  [ProjectPermission.owner]: 'owner'
}

export const PROJECT_PERMISSION_LABEL_BY_NAME: Record<
  ProjectPermissionName,
  string
> = {
  read: 'Read',
  write: 'Write',
  owner: 'Owner'
}

export const PROJECT_PERMISSION_BY_NAME: Record<
  ProjectPermissionName,
  ProjectPermission
> = {
  read: ProjectPermission.read,
  write: ProjectPermission.write,
  owner: ProjectPermission.owner
}

export interface ProjectPermissionValueForSelect {
  label: string
  value: ProjectPermissionName
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

export function getUserRoleValuesForSelect(
  roles: UserRoleName[]
): UserRoleValueForSelect[] {
  return roles.map((role) => ({
    value: role,
    label: USER_ROLE_LABEL_BY_NAME[role]
  }))
}

export function getProjectPermissionValuesForSelect(
  permissions: ProjectPermissionName[]
): ProjectPermissionValueForSelect[] {
  return permissions.map((permission) => ({
    value: permission,
    label: PROJECT_PERMISSION_LABEL_BY_NAME[permission]
  }))
}
