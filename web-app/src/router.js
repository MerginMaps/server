// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import Vue from 'vue'
import Router from 'vue-router'
import AppHeader from '@/components/AppHeader'
import ProjectsList from '@/views/ProjectsList'
import Project from '@/views/Project'
import FileBrowser from '@/views/FileBrowser'
import FileDetail from '@/views/FileDetail'
import ProjectSettings from '@/views/ProjectSettings'
import ProjectVersions from '@/views/ProjectVersions'
import VersionDetail from '@/views/VersionDetail'
import FileVersionDetail from '@/views/FileVersionDetail'
import store from './store'
import UserProjects from '@/user/views/UserProjects'
import Profile from '@/user/views/Profile'
import Organisations from '@/user/views/Organisations'
import Root from '@/user/views/Root'
import OrganisationProfile from '@/organisation/views/OrganisationProfile'
import OrganisationProjects from '@/organisation/views/OrganisationProjects'
import OrganisationMembers from '@/organisation/views/OrganisationMembers'
import Organisation from '@/organisation/views/Organisation'
import LoginDialog from '@/components/LoginDialog'
import Dashboard from './views/Dashboard'
import SideBar from '@/components/SideBar'
import OrganisationSideBar from './organisation/components/OrganisationSideBar'
import { parseError } from '@/mergin'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      beforeEnter: (to, from, next) => {
        if (store.state.app.user) next('/dashboard')
        else next()
      },
      path: '/login/:reset?',
      name: 'login',
      component: LoginDialog,
      props: true,
      meta: { public: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      components: {
        default: Dashboard,
        header: AppHeader,
        sidebar: SideBar
      },
      props: {
        default: true
      }
    },
    {
      path: '/profile',
      name: 'user_profile',
      beforeEnter: (to, from, next) => {
        next(`users/${store.state.app.user.username}/profile`)
      }
    },
    {
      path: '/projects',
      name: 'projects',
      meta: { public: true },
      components: {
        default: ProjectsList,
        header: AppHeader,
        sidebar: SideBar
      },
      props: {
        default: true
      },
      children: [
        {
          path: 'shared',
          name: 'shared_projects',
          component: ProjectsList,
          props: true,
          meta: { flag: 'shared', header: 'Shared with me' }
        },
        {
          path: 'created',
          name: 'my_projects',
          component: ProjectsList,
          props: true,
          meta: { flag: 'created', header: 'My projects' }
        },
        {
          path: 'explore',
          name: 'explore',
          component: ProjectsList,
          props: true,
          meta: { flag: 'explore', header: 'Explore projects' }
        },
        {
          path: 'request',
          name: 'request_projects',
          component: ProjectsList,
          props: true,
          meta: { flag: 'request', header: 'Projects to be transferred' }
        },
        {
          path: ':namespace',
          name: 'namespace-projects',
          component: ProjectsList,
          props: true
        }
      ]
    },
    {
      path: '/projects/:namespace/:projectName',
      name: 'project',
      components: {
        default: Project,
        header: AppHeader,
        sidebar: SideBar
      },
      props: {
        default: true
      },
      redirect: { name: 'project-tree' },
      children: [
        {
          path: 'blob/:location*',
          name: 'blob',
          component: FileDetail,
          props: true
        },
        {
          path: 'tree/:location*',
          name: 'project-tree',
          component: FileBrowser,
          props: true
        },
        {
          path: 'settings',
          name: 'project-settings',
          component: ProjectSettings,
          props: true
        },
        {
          path: 'history',
          name: 'project-versions',
          component: ProjectVersions,
          props: true
        },
        {
          path: 'history/:version_id',
          name: 'project-versions-detail',
          component: VersionDetail,
          props: true
        },
        {
          path: 'history/:version_id/:path',
          name: 'file-version-detail',
          component: FileVersionDetail,
          props: true
        }
      ]
    },
    {
      path: '/users/:name',
      name: 'user',
      components: {
        default: Root,
        header: AppHeader,
        sidebar: SideBar
      },
      beforeEnter: (to, from, next) => {
        if (store.state.app.user.username === to.params.name) next()
        else next({ name: 'user', params: { name: store.state.app.user.username } })
      },
      props: {
        default: true
      },
      children: [
        {
          path: 'profile',
          name: 'profile',
          component: Profile,
          props: true,
          meta: {
            toSidebar: true,
            name: 'Profile'
          }
        },
        {
          path: 'projects',
          name: 'user_projects',
          component: UserProjects,
          props: true
        },
        {
          path: 'organisations',
          name: 'user_organisations',
          components: {
            default: Organisations
          },
          props: true
        }
      ]
    },
    {
      path: '/organisations/:name',
      name: 'organisation',
      components: {
        default: Organisation,
        header: AppHeader,
        sidebar: OrganisationSideBar
      },
      beforeEnter: (to, from, next) => {
        if (store.getters.isUserMemberOfOrganisation(to.params.name)) {
          store.dispatch('setOrganisation', to.params.name)
            .then(next)
            .catch((e) => { next(Error(parseError(e, 'Failed to get organisation'))) })
        } else next(from)
      },
      props: {
        default: true
      },
      children: [
        {
          path: 'profile',
          name: 'org_profile',
          component: OrganisationProfile,
          props: true,
          meta: {
            toSidebar: true,
            name: 'Profile'
          }
        },
        {
          path: 'members',
          name: 'org_members',
          component: OrganisationMembers,
          props: true,
          meta: {
            toSidebar: true,
            name: 'Members'
          }
        },
        {
          path: 'projects',
          name: 'org_projects',
          component: OrganisationProjects,
          props: true
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.meta.public || store.state.app.user) next()
  else next(`/login?redirect=${to.fullPath}`)
})
export default router
