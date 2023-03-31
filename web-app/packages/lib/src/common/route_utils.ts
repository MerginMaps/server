// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import isEqual from 'lodash/isEqual'
import pick from 'lodash/pick'
import { Route, NavigationGuardNext } from 'vue-router'
import { Store } from 'vuex'

export type IsAuthenticatedGuardOptions = {
  notAuthenticatedRedirectPath?: string
}

export function isTheSameRoute(from: Route, to: Route) {
  const properties = ['name', 'path', 'hash', 'params', 'query']
  return isEqual(pick(from, properties), pick(to, properties))
}

export function getTagsFromQuery(route: Route) {
  const tags = route.query.tags
  return tags ? (typeof tags === 'string' ? tags.split(',') : tags) : []
}

/** Handles redirect to /login when user is not authenticated. */
export function isAuthenticatedGuard(
  to: Route,
  from: Route,
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
      query: { redirect: to.fullPath }
    })
  }
}

/** Handles redirect to /login when user is not superUser. */
export function isSuperUser(
  to: Route,
  from: Route,
  next: NavigationGuardNext,
  store: Store<any>
) {
  if (store.getters['userModule/isSuperUser']) {
    next()
  } else {
    next('/login')
  }
}
