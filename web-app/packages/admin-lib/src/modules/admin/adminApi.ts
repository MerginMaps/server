// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// import { getDefaultRetryOptions } from '@mergin/lib'
import {
  ApiRequestSuccessInfo,
  LoginData,
  UserProfileResponse,
  UserResponse /*, getDefaultRetryOptions */
} from '@mergin/lib'
import { AxiosResponse } from 'axios'

import { AdminModule } from '@/modules/admin/module'
import {
  UsersParams,
  UpdateUserData,
  UsersResponse,
  LatestServerVersionResponse,
  CreateUserData
} from '@/modules/admin/types'

export const AdminApi = {
  login: (data: LoginData): Promise<AxiosResponse<void>> =>
    AdminModule.httpService.post('/app/admin/login', data),

  async fetchUsers(params: UsersParams): Promise<AxiosResponse<UsersResponse>> {
    return AdminModule.httpService.get(`/app/admin/users`, { params })
  },

  async fetchUserProfileByName(
    username: string
  ): Promise<AxiosResponse<UserResponse>> {
    return AdminModule.httpService.get(
      `/app/admin/user/${username}?random=${Math.random()}`
    )
  },

  async deleteUser(
    username: number,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return AdminModule.httpService.delete(
      `/app/admin/user/${username}` /*, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    } */
    )
  },

  async updateUser(
    username: string,
    data: UpdateUserData,
    withRetry?: boolean
  ): Promise<AxiosResponse<UserResponse>> {
    return AdminModule.httpService.patch(
      `/app/admin/user/${username}`,
      data /*,
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      } */
    )
  },

  async getServerVersion(): Promise<
    AxiosResponse<LatestServerVersionResponse>
  > {
    return AdminModule.httpService.get('/v1/latest-version')
  },

  // TODO: deprecated?
  /**
   * Update account storage
   * @param accountId (Int) edited account
   * @param data ({Int}) new storage
   * @param withRetry (Boolean)
   * @return Result promise
   */
  async updateAccountStorage(
    accountId: number,
    data: any,
    withRetry?: boolean
  ): Promise<ApiRequestSuccessInfo> {
    const result = {} as ApiRequestSuccessInfo
    try {
      await AdminModule.httpService.post(
        `/app/account/change-storage/${accountId}`,
        data /*,
        {
          ...(withRetry ? getDefaultRetryOptions() : {})
        } */
      )
      result.success = true
    } catch (e) {
      result.success = false
      result.message = e.response.data?.detail || 'Unable to update storage'
    }
    return new Promise((resolve) => {
      resolve(result)
    })
  },

  async createUser(
    data: CreateUserData
  ): Promise<AxiosResponse<UserProfileResponse>> {
    return AdminModule.httpService.post(`/app/admin/user`, data)
  }
}
