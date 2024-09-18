// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  AccountsView,
  AccountDetailView
  //   SettingsView,
  //   ProjectSettingsView,
  //   ProjectsView,
  //   ProjectView,
  //   LoginView,
  //   useAdminStore
} from '@mergin/admin-lib'
import {
  NotFoundView,
  routeUtils,
  // errorUtils,
  // FileBrowserView,
  // ProjectVersionsView,
  // FileVersionDetailView,
  useUserStore
} from '@mergin/lib'
import { Pinia } from 'pinia'
import {
  createRouter as createRouterInstance,
  createWebHistory
} from 'vue-router'

import AppHeader from './modules/layout/components/AppHeader.vue'
import Sidebar from './modules/layout/components/Sidebar.vue'
import { LoginView } from './modules/user'

export const createRouter = (pinia: Pinia) => {
  const router = createRouterInstance({
    history: createWebHistory(),
    routes: [
      {
        path: '/:pathMatch(.*)*',
        component: NotFoundView
      },
      {
        beforeEnter: (to, from, next) => {
          const userStore = useUserStore(pinia)
          if (userStore.isSuperUser) {
            next('/dashboard')
          } else {
            next()
          }
        },
        path: '/login/:reset?',
        name: 'login',
        component: LoginView,
        props: true,
        meta: { public: true }
      },
      {
        path: '/',
        name: 'admin',
        component: NotFoundView,
        beforeEnter: (to, from, next) => {
          next('/accounts')
        },
        props: true
      },
      {
        path: '/accounts',
        name: 'accounts',
        components: {
          default: AccountsView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true,
        beforeEnter: (to, from, next) => {
          const userStore = useUserStore(pinia)
          routeUtils.isAuthenticatedGuard(to, from, next, userStore)
          routeUtils.isSuperUser(to, from, next, userStore)
        }
      },
      {
        path: '/user/:username',
        name: 'account',
        components: {
          default: AccountDetailView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      }
      // {
      //   path: '/projects',
      //   name: 'projects',
      //   component: ProjectsView,
      //   props: true,
      //   children: [
      //     {
      //       path: ':namespace',
      //       name: 'namespace-projects',
      //       component: ProjectsView,
      //       props: true
      //     }
      //   ]
      // },
      // {
      //   path: '/projects/:namespace/:projectName',
      //   name: 'project',
      //   component: ProjectView,
      //   props(route) {
      //     return {
      //       namespace: route.params.namespace,
      //       projectName: route.params.projectName,
      //       asAdmin: true
      //     }
      //   },
      //   redirect: { name: 'project-tree' },
      //   children: [
      //     {
      //       path: 'blob/:location*',
      //       name: 'blob',
      //       component: NotFoundView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName,
      //           location: route.params.location
      //         }
      //       }
      //     },
      //     {
      //       path: 'tree/:location*',
      //       name: 'project-tree',
      //       component: FileBrowserView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName,
      //           location: route.params.location
      //         }
      //       }
      //     },
      //     {
      //       path: 'settings',
      //       name: 'project-settings',
      //       component: ProjectSettingsView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName
      //         }
      //       }
      //     },
      //     {
      //       path: 'history',
      //       name: 'project-versions',
      //       component: ProjectVersionsView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName
      //         }
      //       }
      //     },
      //     {
      //       path: 'history/:version_id',
      //       name: 'project-versions-detail',
      //       component: NotFoundView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName,
      //           version_id: route.params.version_id
      //         }
      //       }
      //     },
      //     {
      //       path: 'history/:version_id/:path',
      //       name: 'file-version-detail',
      //       component: FileVersionDetailView,
      //       props(route) {
      //         return {
      //           asAdmin: true,
      //           namespace: route.params.namespace,
      //           projectName: route.params.projectName,
      //           version_id: route.params.version_id,
      //           path: route.params.path
      //         }
      //       }
      //     }
      //   ]
      // },
      // {
      //   path: '/settings',
      //   name: 'settings',
      //   component: SettingsView,
      //   props: true
      // }
    ]
  })

  /** Handles redirect to /login when user is not authenticated. */
  router.beforeEach((to, from, next) => {
    const userStore = useUserStore(pinia)
    routeUtils.isAuthenticatedGuard(to, from, next, userStore)
    routeUtils.isSuperUser(to, from, next, userStore)
  })

  return router
}
