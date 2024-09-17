// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import isEqual from 'lodash/isEqual'
import pick from 'lodash/pick'
import { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'

export type IsAuthenticatedGuardOptions = {
  notAuthenticatedRedirectPath?: string
}

export function isTheSameRoute(
  from: RouteLocationNormalized,
  to: RouteLocationNormalized
) {
  const properties = ['name', 'path', 'hash', 'params', 'query']
  return isEqual(pick(from, properties), pick(to, properties))
}

export function getTagsFromQuery(route: RouteLocationNormalized) {
  const tags = route.query.tags
  return tags ? (typeof tags === 'string' ? tags.split(',') : tags) : []
}

/** Handles redirect to /login when user is not authenticated. */
export function isAuthenticatedGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
  userStore,
  options?: IsAuthenticatedGuardOptions
) {
  if (to.meta.public || userStore.isLoggedIn) {
    if (isTheSameRoute(from, to)) {
      return false
    } else {
      next()
    }
  } else {
    next({
      path: options?.notAuthenticatedRedirectPath ?? 'login',
      query: { redirect: to.fullPath }
    })
  }
}

/** Handles redirect to /login when user is not superUser. */
export function isSuperUser(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
  userStore
) {
  if (userStore.isSuperUser) {
    next()
  } else {
    next('/login')
  }
}
