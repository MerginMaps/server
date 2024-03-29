// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import VueRouter, { RouteRecord } from 'vue-router'

import { HttpService } from '@/common/http'

export type RouteName = string
export type RouteOverrides = Record<
  RouteName,
  // do not allow to override children
  Partial<Omit<RouteRecord, 'children'>>
>

export interface ModuleService {
  httpService?: HttpService
  routerService?: VueRouter
  [key: string]: any
}

export interface BaseModule {
  name: string
  _addRoutes?: (router, routeOverrides?: RouteOverrides) => void
  init: (services: ModuleService, routeOverrides?: RouteOverrides) => void
}

export interface Module extends BaseModule, ModuleService {}

export interface PaginatedGridOptions {
  sortBy: string[]
  sortDesc: boolean[]
  itemsPerPage: number
  page: number
}

/* eslint-disable camelcase */
/**
 * Request parameters for paginated endpoints
 * TODO: remove legacy order_by and descending in components
 */
export interface PaginatedRequestParams {
  order_by?: string
  order_params?: string
  descending?: boolean
  per_page: number
  page: number
}

/** Stable current request params for paginating endpoints */
export type PaginatedRequestParamsApi = Omit<
  PaginatedRequestParams,
  'order_by' | 'descending'
>

export interface PaginatedResponseDefaults {
  count: number
}
/* eslint-enable camelcase */

export interface PaginatedResponse<T> extends PaginatedResponseDefaults {
  items: readonly T[]
}

export interface ApiRequestSuccessInfo<T = any> {
  success: boolean
  message?: string
  data?: T
}
