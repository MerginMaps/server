// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecordRaw } from 'vue-router'

import { Module, ModuleService, RouteOverrides } from '@/common/types'

export const initializeAppModule = (
  module: Module,
  services?: ModuleService,
  routeOverrides?: RouteOverrides
) => {
  module.init(services, routeOverrides)
}

function elevateToRouteRecordRaw(
  route: Partial<RouteRecordRaw>
): route is RouteRecordRaw {
  return true
}

export function applyRouteOverride(
  route: Partial<RouteRecordRaw>,
  routeOverrides?: RouteOverrides
): Partial<RouteRecordRaw> {
  let overridenRoute = route
  const routeName: string = route.name as unknown as string
  if (overridenRoute.children) {
    overridenRoute.children = route.children.map((child) => {
      const overridenChild = applyRouteOverride(child, routeOverrides)
      let result = child
      // ALWAYS true - this is just hack to cast Partial<RouteRecordRaw> to RouteRecordRaw to get rid of TS error
      if (elevateToRouteRecordRaw(overridenChild)) {
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
