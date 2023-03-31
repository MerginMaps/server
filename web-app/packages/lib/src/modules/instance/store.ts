// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { Module } from 'vuex'

import { InstanceApi } from '@/modules/instance/instanceApi'
import {
  ConfigResponse,
  InitResponse,
  PingResponse
} from '@/modules/instance/types'
import { RootState } from '@/modules/types'

export interface InstanceState {
  initData: InitResponse
  initialized: boolean
  pingData?: PingResponse
  configData?: ConfigResponse
}

const InstanceStore: Module<InstanceState, RootState> = {
  namespaced: true,
  state: {
    initData: undefined,
    initialized: false,
    pingData: undefined,
    configData: undefined
  },
  mutations: {
    setConfigData(state, payload: ConfigResponse) {
      state.configData = payload
    },
    setInitData(state, payload: InitResponse) {
      state.initData = payload
    },
    setPingData(state, payload: PingResponse) {
      state.pingData = payload
    },
    setInitialized(state) {
      state.initialized = true
    }
  },
  actions: {
    async initApp({ commit, dispatch }) {
      try {
        const response = await InstanceApi.getInit()
        commit('setInitData', response.data)
        if (response.data?.authenticated) {
          // fetch user profile if user is logged in
          await dispatch('userModule/fetchUserProfile', undefined, {
            root: true
          })
        }
        commit('setInitialized')
        return response
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to init application.' },
          {
            root: true
          }
        )
      }
    },

    async fetchPing({ commit, dispatch }) {
      try {
        const response = await InstanceApi.getPing()
        commit('setPingData', response.data)
        return response
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to fetch ping data.' },
          {
            root: true
          }
        )
      }
    },

    async fetchConfig({ commit, dispatch }) {
      try {
        const response = await InstanceApi.getConfig()
        commit('setConfigData', response.data)
        return response
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to fetch config data.' },
          {
            root: true
          }
        )
      }
    }
  }
}

export default InstanceStore
