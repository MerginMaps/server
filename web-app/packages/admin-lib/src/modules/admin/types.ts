// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
import {
  PaginatedRequestParams,
  PaginatedResponseDefaults,
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
/* eslint-enable camelcase */
