// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import isEqual from 'lodash/isEqual'
import pick from 'lodash/pick'
import { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { Store } from 'vuex'

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
  store: Store<any>,
  options?: IsAuthenticatedGuardOptions
) {
  if (to.meta.public || store.getters['userModule/isLoggedIn']) {
    if (isTheSameRoute(from, to)) {
      return false
    } else {
      next()
    }
  } else {
    next({
      path: options?.notAuthenticatedRedirectPath ?? 'login',
      // TODO: V3_UPGRADE - check this https://router.vuejs.org/guide/migration/#redirect-records-cannot-use-special-paths
      query: { redirect: to.fullPath }
    })
  }
}

/** Handles redirect to /login when user is not superUser. */
export function isSuperUser(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
  store: Store<any>
) {
  if (store.getters['userModule/isSuperUser']) {
    next()
  } else {
    next('/login')
  }
}
