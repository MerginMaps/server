// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import getRoutes from './routes'

// import store, { ProjectState } from './store'
import { applyRouteOverride } from '@/common/module_utils'
import { Module } from '@/common/types'
import { RootState } from '@/modules/types'

export const ProjectModule: Module<any, RootState> = {
  name: 'projectModule',
  routerService: undefined,
  httpService: undefined,
  // moduleStore: store,
  moduleStore: undefined,
  _addRoutes: (router, rootStore, routeOverrides) => {
    // add routes to router
    getRoutes(rootStore).forEach((route) => {
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
      if (services.store) {
        ProjectModule._addRoutes(
          services.routerService,
          services.store,
          routeOverrides
        )
      }
    }
  }
}
