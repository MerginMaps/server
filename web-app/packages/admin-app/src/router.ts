// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { NotFoundView, routeUtils } from '@mergin/lib'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/:pathMatch(.*)*',
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
