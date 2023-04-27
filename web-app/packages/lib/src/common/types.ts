// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecordRaw, Router } from 'vue-router'
import { Store, Module as VuexModule } from 'vuex'

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
  store?: Store<any>
  [key: string]: any
}

export interface BaseModule<S = any, R = any> {
  name: string
  _addRoutes?: (router, store, routeOverrides?: RouteOverrides) => void
  moduleStore?: VuexModule<S, R>
  init: (services: ModuleService, routeOverrides?: RouteOverrides) => void
}

export interface Module<S = any, R = any>
  extends BaseModule<S, R>,
    ModuleService {}

export interface PaginatedGridOptions {
  sortBy: string[]
  sortDesc: boolean[]
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
