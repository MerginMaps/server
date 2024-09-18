// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  errorUtils,
  htmlUtils,
  LoginPayload,
  SortingOptions,
  useFormStore,
  useInstanceStore,
  useNotificationStore,
  UserResponse
} from '@mergin/lib'
import { defineStore, getActivePinia } from 'pinia'
import Cookies from 'universal-cookie'
import { AdminApi } from '@/modules/admin/adminApi'
import {
  PaginatedAdminProjectsParams,
  UpdateUserPayload,
  UsersResponse
} from '@/modules/admin/types'
import { AdminRoutes } from './routes'

export interface AdminState {
  loading: boolean
  users: {
    items: UserResponse[]
    count: number
  }
  projects: {
    items: any[]
    count: number
    loading: boolean
  }
  user?: UserResponse
  checkForUpdates?: boolean
  info_url?: string
  isServerConfigHidden: boolean
}

const cookies = new Cookies()
const COOKIES_HIDE_SERVER_CONFIGURED_BANNER = 'hideServerConfiguredBanner'

export const useAdminStore = defineStore('adminModule', {
  state: (): AdminState => ({
    loading: false,
    users: {
      items: [],
      count: 0
    },
    projects: {
      items: [],
      count: 0,
      loading: false
    },
    user: null,
    checkForUpdates: undefined,
    info_url: undefined,
    isServerConfigHidden: false
  }),

  getters: {
    displayUpdateAvailable: (state) => {
      return !!state.checkForUpdates
    }
  },

  actions: {
    setLoading(value) {
      this.loading = value
    },
    setUsers(data: UsersResponse) {
      this.users = data
    },
    setCheckForUpdates(value) {
      this.checkForUpdates = value
    },
    setInfoUrl(value: string) {
      this.info_url = value
    },
    setIsServerConfigHidden(value: boolean) {
      this.isServerConfigHidden = value
    },

    async fetchUsers(payload) {
      const notificationStore = useNotificationStore()

      this.setLoading(true)
      try {
        const response = await AdminApi.fetchUsers(payload.params)
        this.setUsers(response.data)
      } catch (e) {
        notificationStore.error({ text: errorUtils.getErrorMessage(e) })
      } finally {
        this.setLoading(false)
      }
    },
    async fetchUserByName(payload) {
      const notificationStore = useNotificationStore()

      htmlUtils.waitCursor(true)
      try {
        const response = await AdminApi.fetchUserByName(payload.username)
        this.user = response.data
      } catch (e) {
        await notificationStore.error({ text: 'Failed to fetch user profile' })
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    async deleteUser(payload) {
      const notificationStore = useNotificationStore()

      htmlUtils.waitCursor(true)
      try {
        await AdminApi.deleteUser(payload.username)
        await getActivePinia().router.push({ name: AdminRoutes.ACCOUNTS })
      } catch (err) {
        await notificationStore.error({
          text: errorUtils.getErrorMessage(err, 'Unable to close account')
        })
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    async updateUser(payload: UpdateUserPayload) {
      const notificationStore = useNotificationStore()

      htmlUtils.waitCursor(true)
      try {
        const response = await AdminApi.updateUser(
          payload.username,
          payload.data
        )
        if (this.user?.id === response.data?.id) {
          // update stored user detail data
          this.user = response.data
        }
      } catch (err) {
        await notificationStore.error({
          text: errorUtils.getErrorMessage(
            err,
            'Unable to permanently remove account'
          )
        })
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    async adminLogin(payload: LoginPayload) {
      const instanceStore = useInstanceStore()
      const formStore = useFormStore()

      try {
        await AdminApi.login(payload.data)
        await instanceStore.initApp()
      } catch (error) {
        await formStore.handleError({
          componentId: payload.componentId,
          error,
          generalMessage: 'Failed to login'
        })
      }
    },

    async checkVersions(payload) {
      try {
        const response = await AdminApi.getServerVersion()
        const { major, minor, fix } = response.data
        // compare payload - major, minor and fix version from config with latest-version from server
        if (
          (payload.major || payload.major === 0) &&
          (payload.minor || payload.minor === 0)
        ) {
          let isUpdate = false
          if (major > payload.major) {
            isUpdate = true
          } else if (major === payload.major) {
            if (minor > payload.minor) {
              isUpdate = true
            } else if (minor === payload.minor) {
              if (fix > payload.fix) {
                isUpdate = true
              }
            }
          }
          if (isUpdate) {
            this.setInfoUrl(response.data.info_url)
          }
        }
      } catch (e) {
        console.error(e)
      }
    },

    async getCheckUpdateFromCookies() {
      const currentCheckForUpdatesCookie = cookies.get('checkUpdates')
      await this.setCheckUpdatesToCookies({
        value:
          currentCheckForUpdatesCookie === undefined
            ? true
            : currentCheckForUpdatesCookie === 'true'
      })
    },

    async setCheckUpdatesToCookies(payload) {
      const expires = new Date()
      // cookies expire in one year
      expires.setFullYear(expires.getFullYear() + 1)
      cookies.set('checkUpdates', payload.value, { expires })
      this.setCheckForUpdates(payload.value)
    },

    async getServerConfiguredCookies() {
      const currentHideServerConfiguredBannerCookie = cookies.get(
        COOKIES_HIDE_SERVER_CONFIGURED_BANNER
      )
      if (currentHideServerConfiguredBannerCookie === 'true') {
        this.setIsServerConfigHidden(true)
      }
    },

    async setServerConfiguredCookies() {
      cookies.set(COOKIES_HIDE_SERVER_CONFIGURED_BANNER, true)
      this.setIsServerConfigHidden(true)
    },

    async removeServerConfiguredCookies() {
      cookies.remove(COOKIES_HIDE_SERVER_CONFIGURED_BANNER)
    },

    async getProjects(payload: {
      params: SortingOptions & Pick<PaginatedAdminProjectsParams, 'like'>
    }) {
      const notificationStore = useNotificationStore()

      try {
        this.projects.loading = true
        const params: PaginatedAdminProjectsParams = {
          page: payload.params.page,
          per_page: payload.params.itemsPerPage,
          order_params: `${payload.params.sortBy[0]} ${
            payload.params.sortDesc[0] ? 'DESC' : 'ASC'
          }`
        }
        if (payload.params.like) {
          params.like = payload.params.like.trim()
        }

        const response = await AdminApi.getProjects(params)
        this.projects.items = response.data.items
        this.projects.count = response.data.count
      } catch (e) {
        notificationStore.error({
          text: 'Failed to fetch projects'
        })
      } finally {
        this.projects.loading = false
      }
    },

    async restoreProject(payload: { projectId: string }) {
      const notificationStore = useNotificationStore()

      try {
        this.projects.loading = true
        await AdminApi.restoreProject(payload.projectId)
      } catch (e) {
        notificationStore.error({
          text: 'Failed to restore project'
        })
      } finally {
        this.projects.loading = false
      }
    },

    async deleteProject(payload: { projectId: string }) {
      const notificationStore = useNotificationStore()

      try {
        await AdminApi.deleteProject(payload.projectId)
        await getActivePinia().router.push({ name: AdminRoutes.PROJECTS })
        notificationStore.show({
          text: 'Project removed successfully'
        })
      } catch (e) {
        notificationStore.error({
          text: 'Unable to remove project'
        })
      }
    }
  }
})
