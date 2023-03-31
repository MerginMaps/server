// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NotFoundView, routeUtils, Router } from '@mergin/lib'
import Vue from 'vue'

import store from './store'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '*',
      component: NotFoundView
    }
  ]
})

/** Handles redirect to /login when user is not authenticated. */
router.beforeEach((to, from, next) => {
  routeUtils.isAuthenticatedGuard(to, from, next, store)
  routeUtils.isSuperUser(to, from, next, store)
})
export default router
