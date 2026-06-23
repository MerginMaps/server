// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded } from 'vue-router'

import returnTranslation from '@/../../lang/translate'

/**
 * Enum for route names in the app's router.
 * Defines string constants for each route path used by project module.
 * Feel free to use it in application router as name attribute and in redirects from lib or app
 */
export enum DashboardRouteName {
  Dashboard = 'dashboard'
}

export const getDashboardTitle = (
  route: RouteLocationNormalizedLoaded,
  extended?: { workspaceName: string }
) => {
  const name = route.name as DashboardRouteName
  const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)
  const titles: Record<DashboardRouteName, string | string[]> = {
    [DashboardRouteName.Dashboard]: [
      t('Dashboard'),
      extended?.workspaceName
    ].filter(Boolean)
  }
  return titles[name]
}
