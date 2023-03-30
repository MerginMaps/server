// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Module } from 'vuex'

import { RootState } from '@/modules/types'

const SNACK_BAR_ERROR_DEFAULT_PARAMS = {
  color: 'red darken-4'
}
const SNACK_BAR_WARN_DEFAULT_PARAMS = {
  color: 'orange',
  buttonColor: 'black'
}

export interface NotificationState {
  isOpen: boolean
  text: string
  params: Record<string, unknown>
}

const NotificationStore: Module<NotificationState, RootState> = {
  namespaced: true,
  state: {
    isOpen: false,
    text: '',
    params: null
  },

  mutations: {
    openNotification(state, payload) {
      state.isOpen = true
      state.text = payload.text
      state.params = payload.params
    },
    closeNotification(state) {
      state.isOpen = false
      state.text = ''
      state.params = null
    }
  },
  actions: {
    show({ commit, dispatch, state }, payload) {
      if (state.isOpen) {
        if (state.text === payload.text) {
          // ignore same notifications
          return
        }
        // previous notification is open, close it first
        commit('closeNotification')
        // show new notification after some time
        setTimeout(() => {
          dispatch('show', { text: payload.text, params: payload.params })
        }, 300)
      } else {
        commit('openNotification', {
          text: payload.text,
          params: payload.params?.timeout
            ? { ...payload.params, timeout: payload.params.timeout }
            : { ...payload.params }
        })
      }
    },
    warn({ dispatch }, payload) {
      dispatch('show', {
        ...payload,
        params: { ...payload.params, ...SNACK_BAR_WARN_DEFAULT_PARAMS }
      })
    },
    error({ dispatch }, payload) {
      dispatch('show', {
        ...payload,
        params: { ...payload.params, ...SNACK_BAR_ERROR_DEFAULT_PARAMS }
      })
    },
    displayResult({ dispatch }, payload) {
      if (payload?.result?.success) {
        dispatch('show', { text: payload?.result?.message })
      } else {
        dispatch('error', {
          text: payload?.result?.message,
          params: { timeout: 5000 }
        })
      }
    }
  }
}

export default NotificationStore
