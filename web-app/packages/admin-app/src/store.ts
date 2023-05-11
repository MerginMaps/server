// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { createPinia, Pinia } from 'pinia'
import Vuex from 'vuex'

let piniaInstance: Pinia | null = null

export const getPiniaInstance = (): Pinia => {
  if (piniaInstance !== null) {
    return piniaInstance
  }

  piniaInstance = createPinia()

  return piniaInstance
}

export default new Vuex.Store({
  strict: import.meta.env.MODE === 'development',
  state: {
    serverError: null // TODO: global - check if used
  },
  mutations: {
    serverError(state, msg) {
      state.serverError = msg
    }
  },
  getters: {},
  actions: {}
})
