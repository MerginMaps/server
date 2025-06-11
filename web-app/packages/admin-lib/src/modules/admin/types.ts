// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
import {
  PaginatedRequestParams,
  PaginatedResponse,
  PaginatedResponseDefaults,
  Project,
  ProjectListItem,
  UserResponse
} from '@mergin/lib'

export interface UsersParams extends PaginatedRequestParams {
  username?: string
}

export type UsersResponse = PaginatedResponse<UserResponse>

export interface UpdateUserData {
  is_admin?: boolean
  active?: boolean
}

export interface CreateUserData {
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
  workspace: string
  workspace_id: number
  updated: string
  version: string
  removed_at: string
  removed_by: string
}

export type PaginatedAdminProjectsResponse =
  PaginatedResponse<AdminProjectListItem>

export interface PaginatedAdminProjectsParams extends PaginatedRequestParams {
  like?: string
}

export type ServerUsageResponse = ServerUsage

export interface ServerUsage {
  active_monthly_contributors: number
  projects: number
  storage: string
  users: number
  workspaces: number
  editors: number
}

export interface DownloadReportParams {
  date_from: string
  date_to: string
}

export interface AdminRouteParams {
  namespace?: string
  projectName?: string
  version_id?: string
  path?: string
  username?: string
}

/* eslint-enable camelcase */
