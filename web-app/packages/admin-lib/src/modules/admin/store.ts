// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import {
  htmlUtils,
  LoginPayload,
  useFormStore,
  useInstanceStore,
  useNotificationStore,
  UserResponse
} from '@mergin/lib'
import { defineStore } from 'pinia'
import Cookies from 'universal-cookie'

import { AdminModule } from './module'

import { AdminApi } from '@/modules/admin/adminApi'
import { UpdateUserPayload } from '@/modules/admin/types'

export interface AdminState {
  loading: boolean
  users: {
    items: UserResponse[]
    count: number
  }
  userAdminProfile?: UserResponse
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
    userAdminProfile: null,
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
    setUsers(data) {
      this.users.count = data.total
      this.users.items = data.users
    },
    setUserAdminProfile(userAdminProfile) {
      this.userAdminProfile = userAdminProfile
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
        notificationStore.error({ text: e.response.data?.detail || e.message })
      } finally {
        this.setLoading(false)
      }
    },
    async fetchUserProfileByName(payload) {
      const notificationStore = useNotificationStore()

      htmlUtils.waitCursor(true)
      try {
        const response = await AdminApi.fetchUserProfileByName(payload.username)
        this.setUserAdminProfile(response.data)
      } catch {
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
        await AdminModule.routerService.push({ name: 'accounts' })
      } catch (err) {
        const msg =
          err.response && err.response.data.detail
            ? err.response.data.detail
            : 'Unable to close account'
        await notificationStore.error({ text: msg })
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
        if (this.userAdminProfile?.id === response.data?.id) {
          // update stored user detail data
          this.setUserAdminProfile(response.data)
        }
        await AdminModule.routerService.push({ name: 'accounts' })
      } catch (err) {
        const msg =
          err.response && err.response.data.detail
            ? err.response.data.detail
            : 'Unable to permanently remove account'
        await notificationStore.error({ text: msg })
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    // TODO: deprecated?
    async updateAccountStorage(_context, payload) {
      return await AdminApi.updateAccountStorage(
        payload.accountId,
        payload.data
      )
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
            commit('setInfoUrl', response.data.info_url)
          }
        }
      } catch (e) {
        console.log(e)
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
    }
  }
})
