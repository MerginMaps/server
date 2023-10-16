// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import getRoutes from './routes'

import { applyRouteOverride } from '@/common/module_utils'
import { Module } from '@/common/types'

export const UserModule: Module = {
  name: 'userModule',
  routerService: undefined,
  httpService: undefined,
  _addRoutes: (router, routeOverrides) => {
    // add routes to router
    getRoutes().forEach((route) => {
      router.addRoute(applyRouteOverride(route, routeOverrides))
    })
  },
  init: (services, routeOverrides) => {
    if (services.httpService) {
      UserModule.httpService = services.httpService
    } else {
      console.error(`Module ${UserModule.name} - missing httpService`)
    }

    if (services.routerService) {
      UserModule.routerService = services.routerService
      UserModule._addRoutes(services.routerService, routeOverrides)
    }
  }
}
