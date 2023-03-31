// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import FileSaver from 'file-saver'

export default {
  methods: {
    /**
     * fetch logged user profile
     * @return user's profile
     */
    // TODO: used only in billing module, use user module action there instead
    async fetchUserProfile(username) {
      await this.$http
        .get(`/v1/user/${username}`)
        .then((resp) => {
          this.$store.commit('updateUserProfile', resp.data)
          this.$store.commit(
            'updateVerifiedEmailFlag',
            resp.data.verified_email
          )
        })
        .catch(() =>
          this.$store.dispatch('notificationModule/error', {
            text: "Failed to fetch user's profile"
          })
        )
    },
    // TODO: transform to project module action
    downloadArchive(url) {
      this.$http
        .get(url, { responseType: 'blob' })
        .then((resp) => {
          const fileName =
            resp.headers['content-disposition'].split('filename=')[1]
          FileSaver.saveAs(resp.data, fileName)
        })
        .catch((e) => {
          // parse error details from blob
          let resp
          const blob = new Blob([e.response.data], { type: 'text/plain' })
          blob.text().then((text) => {
            resp = JSON.parse(text)
            this.$store.dispatch('notificationModule/error', {
              text: resp.detail
            })
          })
        })
    }
  }
}
