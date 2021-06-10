// Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
import store from '../../store'
import Index from '../views/dashboard/Index'
import Account from '../views/dashboard/pages/Account'
import AdminProfile from '../views/dashboard/pages/Profile'
import AdminOrganisationProfile from '../views/dashboard/pages/OrganisationProfile'
import Projects from '../views/dashboard/pages/Projects'
import Project from '@/views/Project'
import AppHeader from '@/components/AppHeader'
import FileBrowser from '@/views/FileBrowser'
import FileDetail from '@/views/FileDetail'
import ProjectSettings from '@/views/ProjectSettings'
import FileVersionDetail from '@/views/FileVersionDetail'
import VersionDetail from '@/views/VersionDetail'
import ProjectVersions from '@/views/ProjectVersions'
import { parseError } from '@/mergin'


import HTTP from '@/http'


export default [
  {
    path: '/admin',
    name: 'admin',
    components: {
      default: Index
    },
    beforeEnter: (to, from, next) => {
      if (store.state.app.user && store.state.app.user.is_admin) next()
      else next('/')
    },
    props: {
      default: true
    },
    children: [
      {
        path: 'accounts',
        name: 'accounts',
        component: Account,
        props: true
      },
      {
        path: 'accounts/:account_id',
        name: 'account',
        component: Account,
        props: true,
        beforeEnter: (to, from, next) => {
          HTTP.get(`/app/accounts/${to.params.account_id}`)
            .then(resp => {
              if (resp.data.type === 'user') {
                next({ name: 'admin-profile', params: { username: resp.data.name } })
              } else {
                next({ name: 'admin-organisation', params: { username: resp.data.name } })
              }
            })
            .catch(() => next(from))
        }
      },
      {
        path: 'user/:username',
        name: 'admin-profile',
        component: AdminProfile,
        props: true,
        beforeEnter: (to, from, next) => {
          store.commit('admin/userAdminProfile', null)
          store.dispatch('admin/fetchUserAdminProfile', to.params.username)
            .then(next())
            .catch((e) => { next(Error(parseError(e, 'Failed to fetch user profile'))) })
        }
      },
      {
        path: 'organisation/:name',
        name: 'admin-organisation',
        component: AdminOrganisationProfile,
        props: true,
        beforeEnter: (to, from, next) => {
          store.commit('organisation', null)
          store.dispatch('setOrganisation', to.params.name)
            .then(next())
            .catch((e) => { next(Error(parseError(e, 'Failed to get organisation'))) })
        }
      },
      {
        path: 'projects',
        name: 'admin-projects',
        component: Projects,
        props: true,
        children: [
          {
            path: ':namespace',
            name: 'admin-namespace-projects',
            component: Projects,
            props: true
          }
        ]
      },
      {
        path: 'projects/:namespace/:projectName',
        name: 'admin-project',
        components: {
          default: Project,
          header: AppHeader
        },
        props: {
          default: route => ({
            namespace: route.params.namespace,
            projectName: route.params.projectName,
            asAdmin: true
          })
        },
        redirect: { name: 'admin-project-tree' },
        children: [
          {
            path: 'blob/:location*',
            name: 'admin-blob',
            component: FileDetail,
            props (route) {
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
            name: 'admin-project-tree',
            component: FileBrowser,
            props (route) {
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
            name: 'admin-project-settings',
            component: ProjectSettings,
            props (route) {
              return {
                asAdmin: true,
                namespace: route.params.namespace,
                projectName: route.params.projectName
              }
            }
          },
          {
            path: 'history',
            name: 'admin-project-versions',
            component: ProjectVersions,
            props (route) {
              return {
                asAdmin: true,
                namespace: route.params.namespace,
                projectName: route.params.projectName
              }
            }
          },
          {
            path: 'history/:version_id',
            name: 'admin-project-versions-detail',
            component: VersionDetail,
            props (route) {
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
            name: 'admin-file-version-detail',
            component: FileVersionDetail,
            props (route) {
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
      }
    ]
  }
]
