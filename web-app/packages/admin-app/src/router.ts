// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NotFoundView, routeUtils, Router } from '@mergin/lib'
import Vue from 'vue'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  base: import.meta.env.BASE_URL,
  routes: [
    {
      path: '*',
      component: NotFoundView
    }
  ]
})

/** Handles redirect to /login when user is not authenticated. */
router.beforeEach((to, from, next) => {
  routeUtils.isAuthenticatedGuard(to, from, next)
  routeUtils.isSuperUser(to, from, next)
})
export default router
