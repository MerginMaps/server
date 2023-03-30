// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { htmlUtils, LoginPayload, UserResponse } from '@mergin/lib'
import Cookies from 'universal-cookie'
import { Module } from 'vuex'

import { AdminApi } from '@/modules/admin/adminApi'
import { AdminModule } from '@/modules/admin/module'
import { UpdateUserPayload } from '@/modules/admin/types'
import { CeAdminLibRootState } from '@/modules/types'

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

const AdminStore: Module<AdminState, CeAdminLibRootState> = {
  namespaced: true,
  state: {
    loading: false,
    users: {
      items: [],
      count: 0
    },
    userAdminProfile: null,
    checkForUpdates: undefined,
    info_url: undefined,
    isServerConfigHidden: false
  },
  mutations: {
    loading(state, value) {
      state.loading = value
    },
    users(state, data) {
      state.users.count = data.total
      state.users.items = data.users
    },
    userAdminProfile(state, userAdminProfile) {
      state.userAdminProfile = userAdminProfile
    },
    setCheckForUpdates(state, value) {
      state.checkForUpdates = value
    },
    setInfoUrl(state, value: string) {
      state.info_url = value
    },
    setIsServerConfigHidden(state, value: boolean) {
      state.isServerConfigHidden = value
    }
  },
  getters: {
    displayUpdateAvailable: (state) => {
      return !!state.checkForUpdates
    }
  },
  actions: {
    async fetchUsers({ commit, dispatch }, payload) {
      commit('loading', true)
      try {
        const response = await AdminApi.fetchUsers(payload.params)
        commit('users', response.data)
      } catch (e) {
        await dispatch(
          'notificationModule/error',
          { text: e.response.data?.detail || e.message },
          {
            root: true
          }
        )
      } finally {
        commit('loading', false)
      }
    },
    async fetchUserProfileByName({ commit, dispatch }, payload) {
      htmlUtils.waitCursor(true)
      try {
        const response = await AdminApi.fetchUserProfileByName(payload.username)
        commit('userAdminProfile', response.data)
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to fetch user profile' },
          {
            root: true
          }
        )
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    async closeAccount({ dispatch }, payload) {
      htmlUtils.waitCursor(true)
      try {
        await AdminApi.closeAccount(payload.username)
        await AdminModule.routerService.push({ name: 'accounts' })
      } catch (err) {
        const msg =
          err.response && err.response.data.detail
            ? err.response.data.detail
            : 'Unable to close account'
        await dispatch(
          'notificationModule/error',
          { text: msg },
          {
            root: true
          }
        )
      } finally {
        htmlUtils.waitCursor(false)
      }
    },

    async updateUser({ commit, dispatch, state }, payload: UpdateUserPayload) {
      htmlUtils.waitCursor(true)
      try {
        const response = await AdminApi.updateUser(
          payload.username,
          payload.data
        )
        if (state.userAdminProfile?.id === response.data?.id) {
          // update stored user detail data
          commit('userAdminProfile', response.data)
        }
        await AdminModule.routerService.push({ name: 'accounts' })
      } catch (err) {
        const msg =
          err.response && err.response.data.detail
            ? err.response.data.detail
            : 'Unable to permanently remove account'
        await dispatch(
          'notificationModule/error',
          { text: msg },
          {
            root: true
          }
        )
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

    async adminLogin({ dispatch }, payload: LoginPayload) {
      try {
        await AdminApi.login(payload.data)
        await dispatch('instanceModule/initApp', undefined, { root: true })
      } catch (error) {
        await dispatch(
          'formModule/handleError',
          {
            componentId: payload.componentId,
            error: error,
            generalMessage: 'Failed to login'
          },
          { root: true }
        )
      }
    },

    async checkVersions({ commit }, payload) {
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

    async getCheckUpdateFromCookies({ dispatch }) {
      const currentCheckForUpdatesCookie = cookies.get('checkUpdates')
      await dispatch('setCheckUpdatesToCookies', {
        value:
          currentCheckForUpdatesCookie === undefined
            ? true
            : currentCheckForUpdatesCookie === 'true'
      })
    },

    async setCheckUpdatesToCookies({ commit }, payload) {
      const expires = new Date()
      // cookies expire in one year
      expires.setFullYear(expires.getFullYear() + 1)
      cookies.set('checkUpdates', payload.value, { expires })
      commit('setCheckForUpdates', payload.value)
    },

    async getServerConfiguredCookies({ commit }) {
      const currentHideServerConfiguredBannerCookie = cookies.get(
        COOKIES_HIDE_SERVER_CONFIGURED_BANNER
      )
      if (currentHideServerConfiguredBannerCookie === 'true') {
        commit('setIsServerConfigHidden', true)
      }
    },

    async setServerConfiguredCookies({ commit }) {
      cookies.set(COOKIES_HIDE_SERVER_CONFIGURED_BANNER, true)
      commit('setIsServerConfigHidden', true)
    },

    async removeServerConfiguredCookies() {
      cookies.remove(COOKIES_HIDE_SERVER_CONFIGURED_BANNER)
    }
  }
}

export default AdminStore
