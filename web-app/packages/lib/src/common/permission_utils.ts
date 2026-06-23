// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { DropdownOption } from './components/types'

import returnTranslation from '@/../../lang/translate'
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

const PROJECT_ROLE_OPTIONS = [
  ['reader', 'read', 'Reader', 'CanViewProjectFiles'],
  ['editor', 'edit', 'Editor', 'CanCollectFeaturesInProject'],
  ['writer', 'write', 'Writer', 'CanEditProjectFiles'],
  ['owner', 'owner', 'Owner', 'CanShareAndRemoveProject']
] as const

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
  const lang = import.meta.env.VITE_LANG

  return PROJECT_ROLE_OPTIONS.map(([value, , label, description]) => ({
    value,
    label: returnTranslation(lang, label),
    description: returnTranslation(lang, description)
  }))
}

export function getProjectPermissionsValues(): DropdownOption<ProjectPermissionName>[] {
  const lang = import.meta.env.VITE_LANG

  return PROJECT_ROLE_OPTIONS.map(([, value, label, description]) => ({
    value,
    label: returnTranslation(lang, label),
    description: returnTranslation(lang, description)
  }))
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
