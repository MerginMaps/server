// Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import { waitCursor } from '../util'
import { postRetryCond } from '../http'

const API_PREFIX = '/v1'
const PROJECT_URL = `${API_PREFIX}/project`

export default {
  methods: {
    /**
     * Fetch project transfers from server
     */
    fetchTransfers (namespace) {
      waitCursor(true)
      this.$http.get(`${PROJECT_URL}/transfer/${namespace}`)
        .then(resp => {
          this.$store.commit('transfers', resp.data)
        })
        .catch(() => this.$notification.error('Failed to fetch projects transfer requests'))
        .finally(() => { waitCursor(false) })
    },
    /**
     * Fetch access requests from server
     */
    fetchAccessRequests () {
      this.$http.get('/app/project/access_requests')
        .then(resp => {
          this.$store.commit('accessRequests', resp.data)
        })
        .catch(() => this.$notification.error('Failed to fetch project access requests'))
    },
    /**
     * Cancel project transfer
     * @param id
     */
    cancelTransfer (item) {
      waitCursor(true)
      this.$http.delete(`${PROJECT_URL}/transfer/${item.id}`, { 'axios-retry': { retries: 5 } })
        .then(() => {
          this.$store.commit('deleteTransfer', item)
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to cancel transfer'
          this.$notification.error(msg)
        })
        .finally(() => { waitCursor(false) })
    },
    /**
     * Accept project transfer
     * @param id
     * @param props
     * @return success
     */
    async acceptTransfer (transfer, props) {
      let success = false
      waitCursor(true)
      await this.$http.post(`${PROJECT_URL}/transfer/${transfer.id}`, props, { 'axios-retry': { retries: 5 } })
        .then((resp) => {
          this.$store.commit('deleteTransfer', transfer)
          success = true
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to accept transfer'
          this.$notification.error(msg)
          success = false
        })
        .finally(() => {
          waitCursor(false)
        })
      return success
    },
    /**
     * send confirmation email to user
     * @param email
     * @return success
     */
    sendConfirmationEmail (email) {
      // todo logic
      this.$http.get('/auth/resend_confirm_email')
        .then(() => {
          this.$notification.show(`Email was sent to address: ${email}`)
        })
        .catch(err => this.handleError(err, 'Failed to send confirmation email, please check your address in user profile settings'))
    },
    /**
     * fetch logged user profile
     * @return user's profile
     */
    async fetchUserProfile (username) {
      await this.$http.get(`/v1/user/${username}`)
        .then(resp => {
          this.$store.commit('updateUserProfile', resp.data)
          this.$store.commit('updateVerifiedEmailFlag', resp.data.verified_email)
        })
        .catch(() => this.$notification.error("Failed to fetch user's profile"))
    },
    /**
     * change account status
     * @param status
     * @param accountId
     * @return success
     */
    changeAccountStatus (accountId, status) {
      this.$http.patch(`/app/change_account_status/${accountId}`, { status: status }, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(resp => {
        })
        .catch(() => this.$notification.error('Failed to change account status'))
    },
    /**
     * Cancel project access request
     * @param item
     */
    cancelProjectAccessRequest (item) {
      waitCursor(true)
      this.$http.delete(`/app/project/access_request/${item.id}`, { 'axios-retry': { retries: 5 } })
        .then(() => {
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to cancel access request'
          this.$notification.error(msg)
        })
        .finally(() => { waitCursor(false) })
    },
    async fetchProject (callback) {
      this.$http(`/v1/project/${this.namespace}/${this.projectName}`)
        .then(resp => {
          this.$store.commit('project', resp.data)
        })
        .catch(resp => {
          callback(resp.response.status)
        })
    }
  }
}
