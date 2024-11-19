// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
export interface InitResponse {
  authenticated: boolean
  superuser?: boolean
}

export interface PingResponse {
  maintenance: boolean
  status: string
}

export interface BaseConfigResponse {
  blacklist_dirs: string[]
  blacklist_files: string[]
  docs_url: string
  serverType: string
  version: string
  major?: number
  minor?: number
  fix?: number
  global_read?: boolean
  global_write?: boolean
  global_admin?: boolean
  enable_superadmin_assignment: boolean
}

export type ConfigResponse = BaseConfigResponse &
  Record<string, string | number | boolean | undefined | null>
/* eslint-enable camelcase */
