# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="confirm">
    <v-card-title>
      <span class="headline">Edit User's Storage</span>
    </v-card-title>
    <v-card-text>
      <p
        class="text-xs-center red--text"
        v-text="error"
      />
      <v-text-field
        autofocus
        type="number"
        label="storage"
        v-model="storage"
        suffix="MB"
        :min="1"
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn class="black--text" @click="$dialog.close">
        Close
      </v-btn>
      <v-btn
        class="primary"
        @click="confirm"
      >
        Submit
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { waitCursor } from '../util'
import { postRetryCond } from '../http'

export default {
  name: 'edit-storage',
  props: {
    userInfo: Object
  },
  data () {
    return {
      storage: null,
      error: null
    }
  },
  created () {
    this.storage = parseInt(this.userInfo.storage_limit / (1024 * 1024))
  },
  methods: {
    confirm () {
      const profile = {
        storage: parseInt(this.storage * 1024 * 1024)
      }
      waitCursor(true)
      this.$http.post(`/auth/user/${this.userInfo.username}`, { profile }, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(resp => {
          waitCursor(false)
          this.$dialog.close()
          this.$router.go()
        })
        .catch((err) => {
          waitCursor(false)
          this.$notification.error(err.response.data.detail || 'Failed to update user storage')
        })
    }
  }
}
</script>
