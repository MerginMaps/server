// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { moduleUtils, Module } from '@mergin/lib-vue2'

import { getRoutes } from './routes'

export const AdminModule: Module = {
  name: 'adminModule',
  routerService: undefined,
  httpService: undefined,
  _addRoutes: (router, routeOverrides) => {
    // add routes to router
    getRoutes().forEach((route) => {
      router.addRoute(moduleUtils.applyRouteOverride(route, routeOverrides))
    })
  },
  init: (services, routeOverrides) => {
    if (services.httpService) {
      AdminModule.httpService = services.httpService
    } else {
      console.error(`Module ${AdminModule.name} - missing httpService`)
    }
    if (services.routerService) {
      AdminModule.routerService = services.routerService
      AdminModule._addRoutes(services.routerService, routeOverrides)
    }
  }
}
