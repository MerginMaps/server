// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  NotFoundView,
  routeUtils,
  Router,
  errorUtils,
  FileDetailView,
  FileBrowserView,
  ProjectVersionsView,
  VersionDetailView,
  FileVersionDetailView,
  useUserStore
} from '@mergin/lib'
import Vue from 'vue'

import {
  AccountView,
  ProfileView,
  SettingsView,
  ProjectSettingsView,
  ProjectsView,
  ProjectView,
  LoginView,
  useAdminStore
} from '@mergin/admin-lib'
import { addRouterToPinia } from './store'
import { Pinia } from 'pinia'

const router = new Router({
  mode: 'history',
  base: import.meta.env.BASE_URL
})

Vue.use(Router)

export const createRouter = (pinia: Pinia) => {
  const routes = [
    {
      path: '*',
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
      alias: '/dashboard',
      beforeEnter: (to, from, next) => {
        next('/accounts')
      },
      props: {
        default: true
      }
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: AccountView,
      props: true,
      beforeEnter: (to, from, next) => {
        const userStore = useUserStore(pinia)
        routeUtils.isAuthenticatedGuard(to, from, next, userStore)
        routeUtils.isSuperUser(to, from, next, userStore)
      }
    },
    {
      path: '/user/:username',
      name: 'profile',
      component: ProfileView,
      props: true,
      beforeEnter: async (to, from, next) => {
        const adminStore = useAdminStore(pinia)
        adminStore.setUserAdminProfile(null)
        try {
          await adminStore.fetchUserProfileByName({
            username: to.params.username
          })
          next()
        } catch (e) {
          next(
            Error(errorUtils.getErrorMessage(e, 'Failed to fetch user profile'))
          )
        }
      }
    },
    {
      path: '/projects',
      name: 'projects',
      component: ProjectsView,
      props: true,
      children: [
        {
          path: ':namespace',
          name: 'namespace-projects',
          component: ProjectsView,
          props: true
        }
      ]
    },
    {
      path: '/projects/:namespace/:projectName',
      name: 'project',
      component: ProjectView,
      props(route) {
        return {
          namespace: route.params.namespace,
          projectName: route.params.projectName,
          asAdmin: true
        }
      },
      redirect: { name: 'project-tree' },
      children: [
        {
          path: 'blob/:location*',
          name: 'blob',
          component: FileDetailView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName,
              location: route.params.location
            }
          }
        },
        {
          path: 'tree/:location*',
          name: 'project-tree',
          component: FileBrowserView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName,
              location: route.params.location
            }
          }
        },
        {
          path: 'settings',
          name: 'project-settings',
          component: ProjectSettingsView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName
            }
          }
        },
        {
          path: 'history',
          name: 'project-versions',
          component: ProjectVersionsView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName
            }
          }
        },
        {
          path: 'history/:version_id',
          name: 'project-versions-detail',
          component: VersionDetailView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName,
              version_id: route.params.version_id
            }
          }
        },
        {
          path: 'history/:version_id/:path',
          name: 'file-version-detail',
          component: FileVersionDetailView,
          props(route) {
            return {
              asAdmin: true,
              namespace: route.params.namespace,
              projectName: route.params.projectName,
              version_id: route.params.version_id,
              path: route.params.path
            }
          }
        }
      ]
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      props: true
    }
  ]

  routes.forEach((route) => {
    router.addRoute(route)
  })

  /** Handles redirect to /login when user is not authenticated. */
  router.beforeEach((to, from, next) => {
    const userStore = useUserStore(pinia)
    routeUtils.isAuthenticatedGuard(to, from, next, userStore)
    routeUtils.isSuperUser(to, from, next, userStore)
  })
  addRouterToPinia(router)

  return router
}

export default router
