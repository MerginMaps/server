// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecord } from 'vue-router'

import { Module, ModuleService, RouteOverrides } from '@/common/types'

export const initializeAppModule = (
  module: Module,
  services?: ModuleService,
  routeOverrides?: RouteOverrides
) => {
  module.init(services, routeOverrides)
}

function elevateToRouteRecord(
  route: Partial<RouteRecord>
): route is RouteRecord {
  return true
}

export function applyRouteOverride(
  route: Partial<RouteRecord>,
  routeOverrides?: RouteOverrides
): Partial<RouteRecord> {
  let overridenRoute = route
  const routeName: string = route.name as unknown as string
  if (overridenRoute.children) {
    overridenRoute.children = route.children.map((child) => {
      const overridenChild = applyRouteOverride(child, routeOverrides)
      let result = child
      // ALWAYS true - this is just hack to cast Partial<RouteRecord> to RouteRecord to get rid of TS error
      if (elevateToRouteRecord(overridenChild)) {
        result = overridenChild
      }
      return result
    })
  } else if (routeOverrides && routeOverrides[routeName]) {
    overridenRoute = { ...overridenRoute, ...routeOverrides[routeName] }
  }

  if (routeOverrides && routeOverrides[routeName]) {
    overridenRoute = { ...overridenRoute, ...routeOverrides[routeName] }
  }
  return overridenRoute
}
