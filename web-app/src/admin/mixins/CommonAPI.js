// Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import { waitCursor } from '../../util'
import http from '@/http'

export default {
  methods: {
    fetchUserProfileByName (username) {
      waitCursor(true)
      this.$http.get(`/auth/user_profile_by_name/${username}?random=${Math.random()}`)
        .then(resp => {
          this.$store.commit('admin/userAdminProfile', resp.data)
        })
        .catch(() => this.$notification.error('Failed to fetch user profile'))
        .finally(() => {
          waitCursor(false)
        })
    },
    closeAccount (accountId) {
      waitCursor(true)
      const promise = this.$http.delete(`/app/account/${accountId}`, { 'axios-retry': { retries: 5 } })
      Promise.resolve(promise).then(() => {
        location.href = '/admin/accounts'
        this.$router.push({ name: 'Accounts' })
      }).catch(err => {
        const msg = (err.response && err.response.data.detail) ? err.response.data.detail : 'Unable to close account'
        this.$notification.error(msg)
      }).finally(() => { waitCursor(false) })
    },
    /**
     * Fetch a list of removed projects based on pagination params
     * @param params (Object) pagination parameters
     * @return Result promise with either data or error
     */
    async fetchRemovedProjects (params) {
      let result = {}
      try {
        const resp = await http.get('/app/removed-project', { params })
        result = { ...resp.data, success: true }
      } catch (e) {
        result.success = false
        result.message = e.response.data.detail || 'Failed to fetch list of removed projects'
      }
      return new Promise((resolve) => { resolve(result) })
    },
    /**
    * Permanently remove project
    * @param id (Int) removed project id
    * @return Result promise
    */
    async removeProject (id) {
      const result = {}
      try {
        await this.$http.delete(`/app/removed-project/${id}`, { 'axios-retry': { retries: 5 } })
        result.success = true
      } catch (e) {
        result.success = false
        result.message = e.response.data.detail || 'Unable to remove project'
      }
      return new Promise((resolve) => { resolve(result) })
    },
    /**
    * Restore removed project
    * @param id (Int) removed project id
    * @return Result promise
    */
    async restoreProject (id) {
      const result = {}
      try {
        await this.$http.post(`/app/removed-project/restore/${id}`, null, { 'axios-retry': { retries: 5 } })
        result.success = true
      } catch (e) {
        result.success = false
        result.message = e.response.data.detail || 'Unable to restore project'
      }
      return new Promise((resolve) => { resolve(result) })
    },
    /**
    * Update account storage
    * @param accountId (Int) edited account
    * @param storage (Int) new storage
    * @return Result promise
    */
    async updateAccountStorage (accountId, storage) {
      const result = {}
      try {
        await this.$http.post(`/app/account/change_storage/${accountId}`, { storage: storage }, { 'axios-retry': { retries: 5 } })
        result.success = true
      } catch (e) {
        result.success = false
        result.message = e.response.data.detail || 'Unable to update storage'
      }
      return new Promise((resolve) => { resolve(result) })
    }
  }
}
