// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteConfig } from 'vue-router'

import { Module, ModuleService, RouteOverrides } from '@/common/types'

export const initializeAppModule = <S, R>(
  module: Module<S, R>,
  services: ModuleService,
  routeOverrides?: RouteOverrides
) => {
  if (services.store) {
    services.store.registerModule(module.name, module.moduleStore)
    module.init(services, routeOverrides)
  }
}

function elevateToRouteConfig(
  route: Partial<RouteConfig>
): route is RouteConfig {
  return true
}

export function applyRouteOverride(
  route: Partial<RouteConfig>,
  routeOverrides?: RouteOverrides
): Partial<RouteConfig> {
  let overridenRoute = route
  if (overridenRoute.children) {
    overridenRoute.children = route.children.map((child) => {
      const overridenChild = applyRouteOverride(child, routeOverrides)
      let result = child
      // ALWAYS true - this is just hack to cast Partial<RouteConfig> to RouteConfig to get rid of TS error
      if (elevateToRouteConfig(overridenChild)) {
        result = overridenChild
      }
      return result
    })
  } else if (routeOverrides && routeOverrides[route.name]) {
    overridenRoute = { ...overridenRoute, ...routeOverrides[route.name] }
  }

  if (routeOverrides && routeOverrides[route.name]) {
    overridenRoute = { ...overridenRoute, ...routeOverrides[route.name] }
  }
  return overridenRoute
}
