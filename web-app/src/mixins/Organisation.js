// Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import { waitCursor } from '../util'
import { postRetryCond } from '../http'

const URL_PREFIX = '/orgs'

export default {
  methods: {
    getUserOrganisations () {
      this.$http.get(`${URL_PREFIX}/?random=${Math.random()}`)
        .then(resp => {
          this.$store.commit('organisations', resp.data)
        })
        .catch(() => {
          this.$notification.error('Failed to load organisations')
        })
    },
    /**
     * Get organisation by name
     * @param name
     */
    async getOrganisation (name) {
      await this.$http.get(`${URL_PREFIX}/${name}`)
        .then(resp => {
          this.$store.commit('organisation', resp.data)
        })
        .catch(() => {
          this.$notification.error('Failed to load organisation')
        })
    },
    /**
     * Delete organisation
     * @param name
     */
    deleteOrganisation (name) {
      waitCursor(true)
      this.$http.delete(`${URL_PREFIX}/${name}`, { 'axios-retry': { retries: 5 } })
        .then(() => {
          this.getUserOrganisations()
        }).catch(err => {
          const msg = (err.response && err.response.status === 503) ? err.response.data.detail : 'Unable to remove organisation'
          this.$notification.error(msg)
        }).finally(() => { waitCursor(false) })
    },
    /**
     * Update organisation members' access lists
     * @param name
     * @param access
     */
    updateMembers (name, access) {
      // TODO: we need some force reload in case of failure (new values already commited in store)
      waitCursor(true)
      this.$http.patch(`${URL_PREFIX}/${name}/access`, access, { 'axios-retry': { retries: 5 } })
        .then(
          this.$store.commit('updateOrganisationMembers', {
            owners: access.owners,
            admins: access.admins,
            writers: access.writers,
            readers: access.readers
          })
        )
        .catch(err => {
          const msg = (err.response && err.response.status === 503) ? err.response.data.detail : 'Failed to save changes'
          this.$notification.error(msg)
        })
        .finally(() => { waitCursor(false) })
    },
    /**
     * Create a new organisation.
     * Should be called from Form as Promise.
     * @param data
     */
    createOrganisation (data) {
      waitCursor(true)
      this.$http.post(`${URL_PREFIX}/`, data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(() => {
          this.$notification.show('Organisation has been created')
        })
        .catch((err) => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to create organisation'
          this.$notification.error(msg)
        })
        .finally(() => { waitCursor(false) })
    },
    /**
     * Edit organisation (for owner only).
     * Should be called from Form as Promise.
     * @param name
     * @param data
     */
    updateOrganisation (name, data) {
      this.$http.patch(`${URL_PREFIX}/${name}`, data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
    },
    /**
     * Edit organisation plan (for mergin admin only).
     * Should be called from Form as Promise.
     * @param name
     * @param data
     */
    updateOrganisationPlan (name, data) {
      this.$http.patch(`${URL_PREFIX}/${name}/plan`, data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
    },
    /**
     * get invitations.
     * @param name subject name
     * @param type type of subject user/org
     */
    getInvitations (type, name) {
      this.$http.get(`${URL_PREFIX}/invitations/${type}/${name}`)
        .then(resp => {
          if (resp.data.length) {
            if (type === 'user') {
              this.$store.commit('invitations', resp.data)
            } else {
              this.$store.commit('orgInvitations', resp.data)
            }
          }
        })
        .catch(() => {
          this.$notification.error('Failed to get invitations')
        })
    },
    /**
     * delete invitation.
     * @param invitation
     */
    removeInvitation (invitation) {
      this.$http.delete(`${URL_PREFIX}/invitation/${invitation.id}`, { 'axios-retry': { retries: 5 } })
        .then(() => {
          this.$store.commit('deleteInvitation', invitation)
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to cancel invitation'
          this.$notification.error(msg)
        })
    },
    /**
     * accept invitation.
     * @param invitation
     */
    acceptInvitation (invitation) {
      this.$http.post(`${URL_PREFIX}/invitation/confirm/${invitation.id}`, { 'axios-retry': { retries: 5 } })
        .then((response) => {
          this.$store.commit('deleteInvitation', invitation)
          this.$store.commit('addOrganisation', response.data)
          this.$router.push({ name: 'org_profile', params: { name: invitation.org_name } })
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to accept invitation'
          this.$notification.error(msg)
        })
    },
    /**
     * create invitation.
     * @param orgName
     * @param username
     */
    inviteUser (orgName, username) {
      const data = {
        org_name: orgName,
        username: username,
        role: 'reader'
      }
      this.$http.post(`${URL_PREFIX}/invitation/create`, data, { 'axios-retry': { retries: 5 } })
        .then(resp => {
          this.$notification.show('Invitation has been sent to user')
          this.$store.commit('addInvitation', resp.data)
        })
        .catch(err => {
          const msg = (err.response) ? err.response.data.detail : 'Failed to send invitation'
          this.$notification.error(msg)
        })
    }
  }
}
