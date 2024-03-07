// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  ChangePasswordView,
  FileBrowserView,
  FileVersionDetailView,
  ProjectVersionsView,
  NotFoundView,
  VerifyEmailView,
  routeUtils,
  useUserStore,
  SideBarTemplate as SideBar,
  ProjectRouteName
} from '@mergin/lib'
import { Pinia } from 'pinia'
import {
  createWebHistory,
  createRouter as createRouterInstance
} from 'vue-router'

import DashboardView from '@/modules/dashboard/views/DashboardView.vue'
import AppHeader from '@/modules/layout/components/AppHeader.vue'
import ProjectCollaboratorsView from '@/modules/project/views/ProjectCollaboratorsView.vue'
import ProjectSettingsView from '@/modules/project/views/ProjectSettingsView.vue'
import ProjectsListView from '@/modules/project/views/ProjectsListView.vue'
import ProjectView from '@/modules/project/views/ProjectView.vue'
import LoginView from '@/modules/user/views/LoginView.vue'
import ProfileView from '@/modules/user/views/ProfileView.vue'

export const createRouter = (pinia: Pinia) => {
  const router = createRouterInstance({
    history: createWebHistory(),
    routes: [
      {
        path: '/',
        name: 'home',
        meta: { public: true },
        redirect: null,
        beforeEnter: (to, from, next) => {
          const userStore = useUserStore(pinia)
          if (userStore.isLoggedIn) {
            next('/dashboard')
          } else {
            next('/login')
          }
        }
      },
      {
        beforeEnter: (to, from, next) => {
          const userStore = useUserStore(pinia)
          if (userStore.isLoggedIn) {
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
        path: '/confirm-email/:token',
        name: 'confirm_email',
        component: VerifyEmailView,
        props: true,
        meta: { public: true }
      },
      {
        path: '/change-password/:token',
        name: 'change_password',
        component: ChangePasswordView,
        props: true,
        meta: { public: true }
      },
      {
        path: '/dashboard',
        name: 'dashboard',
        components: {
          default: DashboardView,
          header: AppHeader,
          sidebar: SideBar
        },
        meta: {
          breadcrump: [{ title: 'Dashboard', path: '/dashboard' }]
        },
        props: {
          default: true
        }
      },
      {
        path: '/profile',
        name: 'user_profile',
        meta: {
          allowedForNoWorkspace: true,
          breadcrump: [{ title: 'Profile', path: '/profile' }]
        },
        components: {
          default: ProfileView,
          header: AppHeader,
          sidebar: SideBar
        },
        props: true
      },
      {
        path: '/projects',
        name: 'projects',
        components: {
          default: ProjectsListView,
          header: AppHeader,
          sidebar: SideBar
        },
        props: {
          default: true
        },
        meta: {
          public: true,
          title: 'Projects',
          breadcrump: [{ title: 'Projects', path: '/projects' }]
        },
        children: [
          {
            path: 'explore',
            name: 'explore',
            component: ProjectsListView,
            props: true,
            meta: {
              public: true,
              breadcrump: [{ title: 'Explore', path: '/projects/explore' }]
            }
          },
          {
            path: ':namespace',
            name: 'namespace-projects',
            component: ProjectsListView,
            props: true
          }
        ]
      },
      /** Redirect of unused /blob path to /tree */
      {
        path: '/projects/:namespace/:projectName/blob/:location?',
        name: 'blob',
        component: NotFoundView,
        props: true,
        meta: { public: true },
        beforeEnter: (to, from, next) => {
          next({
            path: `/projects/${to.params.namespace}/${
              to.params.projectName
            }/tree${from.params.location ? `/${from.params.location}` : ''}`,
            query: { file_path: to.params.location }
          })
        }
      },
      /** Redirect of unused /history/:version_id path to /history?version_id */
      {
        path: '/projects/:namespace/:projectName/history/:version_id',
        name: 'project-versions-detail',
        component: NotFoundView,
        props: true,
        meta: { public: true },
        beforeEnter: (to, from, next) => {
          next({
            path: `/projects/${to.params.namespace}/${to.params.projectName}/history`,
            query: { version_id: to.params.version_id }
          })
        }
      },
      {
        path: '/projects/:namespace/:projectName',
        name: 'project',
        components: {
          default: ProjectView,
          header: AppHeader,
          sidebar: SideBar
        },
        props: {
          default: true
        },
        meta: {
          breadcrump: [{ title: 'Projects', path: '/projects' }]
        },
        redirect: { name: 'project-tree' },

        children: [
          {
            path: 'tree/:location?',
            name: 'project-tree',
            component: FileBrowserView,
            props: true,
            meta: { public: true }
          },
          {
            path: 'settings',
            name: 'project-settings',
            component: ProjectSettingsView,
            props: true
          },
          {
            path: 'history',
            name: 'project-versions',
            component: ProjectVersionsView,
            props: true
          },
          {
            path: 'collaborators',
            name: ProjectRouteName.ProjectCollaborators,
            component: ProjectCollaboratorsView,
            props: true
          },
          {
            path: 'history/:version_id/:path',
            name: 'file-version-detail',
            component: FileVersionDetailView,
            props: true,
            meta: { public: true },
            // TODO: refactor to function in utils
            beforeEnter(to, from, next) {
              to.meta = {
                ...to.meta,
                breadcrump: [
                  {
                    title: String(to.params.projectName),
                    path: `/projects/${to.params.namespace}/${to.params.projectName}/history`
                  },
                  {
                    title: String(to.params.version_id),
                    path: `/projects/${to.params.namespace}/${to.params.projectName}/history/${to.params.version_id}`
                  },
                  {
                    title: String(to.params.path),
                    path: to.fullPath
                  }
                ]
              }
              next()
            }
          }
        ]
          // Not apply for project version detail , which have own breadcrump
          .map((child) =>
            child.name === 'file-version-detail'
              ? child
              : {
                  ...child,
                  beforeEnter: (to, from, next) => {
                    to.meta = {
                      ...to.meta,
                      breadcrump: [
                        {
                          title: String(to.params.projectName),
                          path: to.fullPath
                        }
                      ]
                    }
                    next()
                  }
                }
          )
      },
      {
        path: '/:pathMatch(.*)*',
        component: NotFoundView,
        meta: { public: true }
      }
    ]
  })

  /** Handles redirect to /login when user is not authenticated. */
  router.beforeEach((to, from, next) => {
    const userStore = useUserStore(pinia)
    routeUtils.isAuthenticatedGuard(to, from, next, userStore)
  })
  return router
}
