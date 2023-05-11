// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import getRoutes from './routes'

// import store, { UserState } from './store'
import { applyRouteOverride } from '@/common/module_utils'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const UserModule: Module<any, RootState> = {
  name: 'userModule',
  routerService: undefined,
  httpService: undefined,
  moduleStore: undefined,
  // moduleStore: store,
  _addRoutes: (router, rootStore, routeOverrides) => {
    // add routes to router
    getRoutes(rootStore).forEach((route) => {
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
      if (services.store) {
        UserModule._addRoutes(
          services.routerService,
          services.store,
          routeOverrides
        )
      }
    }
  }
}
