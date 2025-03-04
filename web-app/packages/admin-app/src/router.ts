// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  AccountsView,
  AccountDetailView,
  SettingsView,
  ProjectsView,
  ProjectView,
  AdminRoutes,
  ProjectFilesView,
  ProjectSettingsView,
  ProjectVersionView,
  ProjectVersionsView,
  OverviewView
} from '@mergin/admin-lib'
import {
  NotFoundView,
  routeUtils,
  FileVersionDetailView,
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
    history: createWebHistory(import.meta.env.BASE_URL),
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
        redirect: '/overview'
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
        path: '/projects/:namespace/:projectName/history/:version_id',
        name: AdminRoutes.ProjectVersion,
        components: {
          default: ProjectVersionView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/projects/:namespace/:projectName/history/:version_id/:path',
        name: AdminRoutes.FileVersionDetail,
        components: {
          default: FileVersionDetailView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/projects/:namespace/:projectName?',
        components: {
          default: ProjectView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true,
        children: [
          {
            path: '',
            name: AdminRoutes.PROJECT,
            component: ProjectFilesView,
            props: true
          },
          {
            path: 'tree/:location?',
            name: AdminRoutes.ProjectTree,
            component: ProjectFilesView,
            props: true
          },
          {
            path: 'settings',
            name: AdminRoutes.ProjectSettings,
            component: ProjectSettingsView,
            props: true
          },
          {
            path: 'history',
            name: AdminRoutes.ProjectHistory,
            component: ProjectVersionsView,
            props: true
          }
        ]
      },
      {
        path: '/settings',
        name: AdminRoutes.SETTINGS,
        components: {
          default: SettingsView,
          sidebar: Sidebar,
          header: AppHeader
        },
        props: true
      },
      {
        path: '/overview',
        name: AdminRoutes.OVERVIEW,
        components: {
          default: OverviewView,
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
