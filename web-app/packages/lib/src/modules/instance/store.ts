// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'

import { InstanceApi } from '@/modules/instance/instanceApi'
import {
  ConfigResponse,
  InitResponse,
  PingResponse
} from '@/modules/instance/types'
import { useNotificationStore } from '@/modules/notification/store'
import { useUserStore } from '@/modules/user/store'

export interface InstanceState {
  initData: InitResponse
  initialized: boolean
  pingData?: PingResponse
  configData?: ConfigResponse
}

export const useInstanceStore = defineStore('instanceModule', {
  state: (): InstanceState => ({
    initData: undefined,
    initialized: false,
    pingData: undefined,
    configData: undefined
  }),

  actions: {
    setConfigData(payload: ConfigResponse) {
      this.configData = payload
    },
    setInitData(payload: InitResponse) {
      this.initData = payload
    },
    setPingData(payload: PingResponse) {
      this.pingData = payload
    },
    setInitialized() {
      this.initialized = true
    },
    async initApp() {
      const notificationStore = useNotificationStore()
      try {
        const response = await InstanceApi.getInit()
        this.setInitData(response.data)
        const userStore = useUserStore()
        if (response.data?.authenticated) {
          // fetch user profile if user is logged in
          await userStore.fetchUserProfile()
        }
        this.setInitialized()
        return response
      } catch {
        notificationStore.error({ text: 'Failed to init application.' })
      }
    },

    async fetchPing() {
      const notificationStore = useNotificationStore()
      try {
        const response = await InstanceApi.getPing()
        this.setPingData(response.data)
        return response
      } catch {
        await notificationStore.error({ text: 'Failed to fetch ping data.' })
      }
    },

    async fetchConfig() {
      const notificationStore = useNotificationStore()
      try {
        const response = await InstanceApi.getConfig()
        this.setConfigData(response.data)
        return response
      } catch {
        await notificationStore.error({ text: 'Failed to fetch config data.' })
      }
    }
  }
})
