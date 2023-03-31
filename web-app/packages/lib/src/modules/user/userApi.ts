// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'

import { getDefaultRetryOptions } from '@/common/http'
import { UserModule } from '@/modules/user/module'
import {
  WorkspaceResponse,
  ChangePasswordWithTokenParams,
  LoginData,
  UserResponse,
  ResetPasswordData,
  UserDetailResponse,
  UserSearch,
  UserSearchParams,
  EditUserProfileParams,
  ChangePasswordParams
} from '@/modules/user/types'

export const UserApi = {
  getAuthUserSearch: (
    params: UserSearchParams
  ): Promise<AxiosResponse<UserSearch[]>> => {
    return UserModule.httpService.get('/app/auth/user/search', { params })
  },

  getAuthUserByUserName: (
    userName: string
  ): Promise<AxiosResponse<UserResponse>> => {
    return UserModule.httpService.get(
      `/app/auth/user/${userName}?random=${Math.random()}`
    )
  },

  editUserProfile: (
    data: EditUserProfileParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> => {
    return UserModule.httpService.post('/app/auth/user/profile', data, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  closeUserProfile: (withRetry?: boolean): Promise<AxiosResponse<void>> => {
    return UserModule.httpService.delete('/v1/user', {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  changePasswordWithToken: (
    token: string,
    data: ChangePasswordWithTokenParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> => {
    return UserModule.httpService.post(
      `/app/auth/reset-password/${token}`,
      data,
      { ...(withRetry ? getDefaultRetryOptions() : {}) }
    )
  },

  changePassword: (data: ChangePasswordParams, withRetry?: boolean) => {
    return UserModule.httpService.post('/app/auth/change-password', data, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  resetPassword: (data: ResetPasswordData): Promise<AxiosResponse<void>> => {
    return UserModule.httpService.post('/app/auth/reset-password', data)
  },

  // TODO: deprecated?
  confirmEmail: (token: string): Promise<AxiosResponse<any>> => {
    return UserModule.httpService.post(`/app/auth/confirm-email/${token}`)
  },

  resendEmail: (): Promise<AxiosResponse<void>> => {
    return UserModule.httpService.get('/app/auth/resend-confirm-email')
  },

  login: (data: LoginData): Promise<AxiosResponse<UserResponse>> =>
    UserModule.httpService.post('/app/auth/login', data),

  logout: (): Promise<AxiosResponse<void>> =>
    UserModule.httpService.get('/app/auth/logout'),

  fetchUserProfile: (): Promise<AxiosResponse<UserDetailResponse>> => {
    return UserModule.httpService.get(`/v1/user/profile`)
  },

  async getWorkspaces(): Promise<AxiosResponse<WorkspaceResponse[]>> {
    return UserModule.httpService.get(`/v1/workspaces`)
  },

  async getWorkspaceById(
    id: number
  ): Promise<AxiosResponse<WorkspaceResponse>> {
    return UserModule.httpService.get(`/v1/workspace/${id}`)
  }
}
