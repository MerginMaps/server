// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
import {
  PaginatedRequestParams,
  PaginatedResponseDefaults,
  Project,
  ProjectListItem,
  UserResponse
} from '@mergin/lib'

export interface UsersParams extends PaginatedRequestParams {
  username?: string
}

export interface UsersResponse extends PaginatedResponseDefaults {
  users: UserResponse[]
}

export interface UpdateUserData {
  is_admin: boolean
  active: boolean
}

export interface CreateUserData {
  username: string
  email: string
  password: string
  confirm: string
}

export interface UpdateUserPayload {
  username: string
  data: UpdateUserData
}

export type ServerVersion = 'ce' | 'ee' | 'saas'

export interface LatestServerVersionResponse {
  major: number
  minor: number
  fix?: number

  version: string
  info_url: string
}

export interface PaginatedProjectsResponse extends PaginatedResponseDefaults {
  projects: ProjectListItem[]
}

export interface AdminProjectListItem extends Project {
  disk_usage: number
  id: string
  name: string
  namespace: string
  updated: string
  version: string
  removed_at: string
  removed_by: string
}

export interface PaginatedAdminProjectsResponse
  extends PaginatedResponseDefaults {
  projects: AdminProjectListItem[]
}

export interface PaginatedAdminProjectsParams extends PaginatedRequestParams {
  workspace?: string
  name?: string
}
/* eslint-enable camelcase */
