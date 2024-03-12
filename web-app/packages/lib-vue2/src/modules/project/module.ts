// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import getRoutes from './routes'

import { applyRouteOverride } from '@/common/module_utils'
import { Module } from '@/common/types'

export const ProjectModule: Module = {
  name: 'projectModule',
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
      ProjectModule.httpService = services.httpService
    } else {
      console.error(`Module ${ProjectModule.name} - missing httpService`)
    }

    if (services.routerService) {
      ProjectModule.routerService = services.routerService
      ProjectModule._addRoutes(services.routerService, routeOverrides)
    }
  }
}
