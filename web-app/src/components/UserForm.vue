# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="createUser">
    <v-card-title>
      <span class="headline">New user</span>
    </v-card-title>
    <v-card-text>
      <v-text-field
        autofocus
        label="username"
        v-model="username"
        :error-messages="errors.username"
      />
      <v-text-field
        label="email"
        v-model="email"
        :error-messages="errors.email"
      />
      <p
        v-if="errorMsg"
        class="text-xs-center red--text"
        v-text="errorMsg"
      />
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close">
        Close
      </v-btn>
      <v-btn
        class="primary"
        :disabled="!username || !email"
        @click="createUser"
      >
        Register
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import FormMixin from '@/mixins/Form'
import { postRetryCond } from '../http'
import { waitCursor } from '../util'

export default {
  mixins: [FormMixin],
  data () {
    return {
      username: '',
      email: ''
    }
  },
  methods: {
    createUser () {
      this.clearErrors()
      const data = {
        username: this.username,
        email: this.email
      }
      waitCursor(true)
      this.$http.post('/auth/user', data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(() => {
          waitCursor(false)
          this.$dialog.close()
          this.$emit('submit')
        })
        .catch(err => {
          waitCursor(false)
          this.handleError(err, 'Failed to send confirmation email')
        })
    }
  }
}
</script>
