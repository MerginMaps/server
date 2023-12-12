// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  ChangePasswordView,
  FileBrowserView,
  FileDetailView,
  FileVersionDetailView,
  ProjectVersionsView,
  VersionDetailView,
  NotFoundView,
  VerifyEmailView,
  routeUtils,
  useUserStore,
  SideBarTemplate as SideBar
} from '@mergin/lib'
import { Pinia } from 'pinia'

import DashboardView from '@/modules/dashboard/views/DashboardView.vue'
import AppHeader from '@/modules/layout/components/AppHeader.vue'
import ProjectSettingsView from '@/modules/project/views/ProjectSettingsView.vue'
import ProjectsListView from '@/modules/project/views/ProjectsListView.vue'
import ProjectView from '@/modules/project/views/ProjectView.vue'
import LoginView from '@/modules/user/views/LoginView.vue'
import ProfileView from '@/modules/user/views/ProfileView.vue'
import {
  createWebHistory,
  createRouter as createRouterInstance
} from 'vue-router'

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
          title: 'Dashboard'
        },
        props: {
          default: true
        }
      },
      {
        path: '/profile',
        name: 'user_profile',
        meta: { allowedForNoWorkspace: true, title: 'Profile' },
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
        meta: { public: true, title: 'Projects' },
        children: [
          {
            path: 'explore',
            name: 'explore',
            component: ProjectsListView,
            props: true,
            meta: { public: true }
          },
          {
            path: ':namespace',
            name: 'namespace-projects',
            component: ProjectsListView,
            props: true
          }
        ]
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
          title: 'Projects'
        },
        redirect: { name: 'project-tree' },
        children: [
          {
            path: 'blob/:location*',
            name: 'blob',
            component: FileDetailView,
            props: true,
            meta: { public: true }
          },
          {
            path: 'tree/:location*',
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
            path: 'history/:version_id?',
            name: 'project-versions-detail',
            component: VersionDetailView,
            props: true
          },
          {
            path: 'history/:version_id?/:path?',
            name: 'file-version-detail',
            component: FileVersionDetailView,
            props: true,
            meta: { public: true }
          }
        ].map((child) => ({
          ...child,
          beforeEnter: (to, from, next) => {
            to.meta.title = to.params.projectName as string
            next()
          }
        }))
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
