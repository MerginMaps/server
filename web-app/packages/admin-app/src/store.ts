// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Vuex from 'vuex'

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
