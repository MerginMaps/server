// Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
import http from '@/http'

export default {
  namespaced: true,
  state: {
    loading: false,
    error: '',
    accounts: {
      items: [],
      count: 0
    },
    userAdminProfile: null
  },
  mutations: {
    loading (state, value) {
      state.loading = value
    },
    error (state, message) {
      state.error = message
    },
    accounts (state, data) {
      state.accounts.count = data.total
      state.accounts.items = data.accounts
    },
    userAdminProfile (state, userAdminProfile) {
      state.userAdminProfile = userAdminProfile
    }
  },
  actions: {
    fetchAccounts ({ commit }, { type, params }) {
      commit('loading', true)
      http.get(`/app/accounts/${type}`, { params })
        .then(resp => {
          commit('accounts', resp.data)
          commit('error', '')
        })
        .catch((e) => {
          commit('error', e.response.data.detail || e.message)
        })
        .finally(() => commit('loading', false))
    },
    async fetchUserAdminProfile ({ commit }, username) {
      const resp = await http.get(`/auth/user_profile_by_name/${username}?random=${Math.random()}`)
      commit('userAdminProfile', resp.data)
    }
  }
}
