// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Route } from 'vue-router'

import { PaginatedRequestParams } from '@/common'
import { UserRoleName } from '@/common/permission_utils'
import { MerginComponentUuidPayload } from '@/modules/form/types'

export interface LoginData {
  login: string
  password: string
}

export interface LoginPayload extends MerginComponentUuidPayload {
  data: LoginData
  currentRoute: Route
}

export interface ResetPasswordPayload extends MerginComponentUuidPayload {
  email: string
}

export interface ResetPasswordData {
  email: string
}

/* eslint-disable camelcase */
export interface UserProfileResponse {
  first_name: string
  has_project: boolean
  last_name: string
  name: string
  receive_notifications: boolean
  registration_date: string
}

export interface UserResponse {
  active: boolean
  email: string
  id: number
  is_admin: boolean
  profile: UserProfileResponse
  username: string
  verified_email: boolean
}

export interface UserWorkspace {
  id: number
  name: string
  role: UserRoleName
}

export interface UserDetailResponse extends UserProfileResponse {
  id: number
  username: string
  email: string
  verified_email: boolean
  first_name: string
  last_name: string
  name: string
  preferred_workspace: number
  receive_notifications: boolean
  registration_date: string
  workspaces: UserWorkspace[]
}

export interface WorkspaceResponse extends UserWorkspace {
  description: string
  project_count: number
  disk_usage: number
  storage: number
}

export interface UserSearch {
  id: number
  profile: {
    first_name: string
    last_name: string
  }
  username: string
  email: string
  permission?: string
}

export interface UserSearchParams {
  id?: string
  names?: string
  like?: string
  namespace: string
}

export interface ChangePasswordWithTokenParams {
  password: string
  confirm: string
}

export interface ChangePasswordWithTokenPayload
  extends MerginComponentUuidPayload {
  data: ChangePasswordWithTokenParams
  token: string
  callback: (value: boolean) => void
}

export interface EditUserProfileParams {
  receive_notifications: boolean
  first_name: string
  last_name: string
  email: string
}

export interface ChangePasswordParams {
  old_password: string
  password: string
  confirm: string
}

export interface ChangePasswordPayload extends MerginComponentUuidPayload {
  data: ChangePasswordParams
}

export interface PaginatedUsersParams extends PaginatedRequestParams {
  like?: string
}

export interface WorkspaceIdPayload {
  id: number
}

export interface IsWorkspaceAdminPayload {
  id: number
}

export interface SetWorkspaceIdPayload {
  workspaceId: number
  skipSavingInCookies?: boolean
}

export interface DeleteAccountConfirmProps {
  username: string
}

/* eslint-enable camelcase */
