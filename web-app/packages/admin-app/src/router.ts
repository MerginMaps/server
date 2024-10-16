// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  AccountsView,
  AccountDetailView,
  SettingsView,
  ProjectsView,
  ProjectView,
  AdminRoutes
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
        path: '/login/:reset?',
        name: 'login',
        component: LoginView,
        props: true,
        meta: { public: true }
      },
      {
        path: '/',
        name: 'admin',
        redirect: '/accounts'
      },
      {
        path: '/accounts',
        name: AdminRoutes.ACCOUNTS,
        components: {
          default: AccountsView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/user/:username',
        name: AdminRoutes.ACCOUNT,
        components: {
          default: AccountDetailView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/projects',
        name: AdminRoutes.PROJECTS,
        components: {
          default: ProjectsView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/projects/:namespace/:projectName?',
        name: AdminRoutes.PROJECT,
        components: {
          default: ProjectView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },

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
      {
        path: '/settings',
        name: AdminRoutes.SETTINGS,
        components: {
          default: SettingsView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      }
    ]
  })

  /** Handles redirect to /login when user is not authenticated. */
  router.beforeEach((to, from, next) => {
    const userStore = useUserStore(pinia)
    routeUtils.isSuperUser(to, from, next, userStore)
  })

  return router
}
