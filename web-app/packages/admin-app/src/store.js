// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  strict: process.env.NODE_ENV === 'development',
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
