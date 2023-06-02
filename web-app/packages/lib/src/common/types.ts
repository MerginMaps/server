// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecordRaw, Router } from 'vue-router'

import { HttpService } from '@/common/http'

export type RouteName = string
export type RouteOverrides = Record<
  RouteName,
  // do not allow to override children
  Partial<Omit<RouteRecordRaw, 'children'>>
>

export interface ModuleService {
  httpService?: HttpService
  routerService?: Router
  [key: string]: any
}

export interface BaseModule {
  name: string
  _addRoutes?: (router, routeOverrides?: RouteOverrides) => void
  init: (services: ModuleService, routeOverrides?: RouteOverrides) => void
}

export interface Module extends BaseModule, ModuleService {}

export interface PaginatedGridOptions {
  sortBy: string
  sortDesc: boolean
  itemsPerPage: number
  page: number
}

/* eslint-disable camelcase */
export interface PaginatedRequestParams {
  order_by?: string
  order_params?: string
  descending?: boolean
  per_page: number
  page: number
}

export interface PaginatedResponseDefaults {
  count: number
}
/* eslint-enable camelcase */

export interface ApiRequestSuccessInfo<T = any> {
  success: boolean
  message?: string
  data?: T
}
