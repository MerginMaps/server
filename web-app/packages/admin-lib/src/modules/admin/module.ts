// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { moduleUtils, Module } from '@mergin/lib'

import getRoutes from './routes'
import store, { AdminState } from './store'
import { CeAdminLibRootState } from '@/modules/types'

export const AdminModule: Module<AdminState, CeAdminLibRootState> = {
  name: 'adminModule',
  routerService: undefined,
  httpService: undefined,
  moduleStore: store,
  _addRoutes: (router, rootStore, routeOverrides) => {
    // add routes to router
    getRoutes(rootStore).forEach((route) => {
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
      if (services.store) {
        AdminModule._addRoutes(
          services.routerService,
          services.store,
          routeOverrides
        )
      }
    }
  }
}
