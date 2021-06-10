# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="createProject">
    <v-card-title>
      <span class="headline">Change password</span>
    </v-card-title>
    <v-card-text>
      <p
        v-if="errorMsg"
        class="text-xs-center red--text"
        v-text="errorMsg"
      />
      <v-form class="layout column">
        <v-text-field
            label="Old Password"
            name="oldPassword"
            color="orange"
            v-model="oldPassword"
            :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
            @click:append="passwordVisible = !passwordVisible"
            :type="passwordVisible ? 'text' : 'password'"
            :error-messages="errors.old_password"
            v-on="on"
          />
        <v-text-field
          label="New Password"
          name="password"
          color="orange"
          v-model="password"
          :type="passwordVisible ? 'text' : 'password'"
          :error-messages="errors.password"
          @keyup.enter="changePassword"
        />
        <v-text-field
          label="Confirm New Password"
          name="confirm"
          color="orange"
          v-model="confirm"
          :type="passwordVisible ? 'text' : 'password'"
          :error-messages="errors.confirm"
          @keyup.enter="changePassword"
        />
        <v-layout row class="d-flex flex-row-reverse">
          <v-tooltip
            top
            color="orange"
            max-width="350"
            content-class="form-tooltip"
          >
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" class="ml-1 mb-1" style="margin-right: 1rem;">info</v-icon>
          </template>
            <ul>
              <li>Password must be at least 8 characters long.</li>
              <li>Password must contain at least 3 character categories among the following:
                <ul>
                  <li>Lowercase characters (a-z)</li>
                  <li>Uppercase characters (A-Z)</li>
                  <li>Digits (0-9)</li>
                  <li>Special characters</li>
                </ul>
              </li>
            </ul>
          </v-tooltip>
        </v-layout>

        <v-card-actions>
          <v-spacer/>
          <v-btn
              class="text--primary"
              @click="$dialog.close"
          >
            Close
          </v-btn>
          <v-btn
            class="primary text--white"
            :disabled="!password || !oldPassword || !confirm"
            @click="changePassword"
          >
            Change
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
import FormMixin from '@/mixins/Form'
import { waitCursor } from '../../util'
import { postRetryCond } from '../../http'

export default {
  mixins: [FormMixin],
  data () {
    return {
      oldPassword: '',
      password: '',
      confirm: '',
      passwordVisible: false
    }
  },
  methods: {
    changePassword () {
      this.clearErrors()
      const data = {
        old_password: this.oldPassword,
        password: this.password,
        confirm: this.confirm
      }
      waitCursor(true)
      this.$http.post('/auth/change_password', data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then(() => {
          this.$dialog.close()
          waitCursor(false)
          this.$notification.show('Password has been changed')
        })
        .catch(err => {
          this.handleError(err, 'Failed to change password')
          waitCursor(false)
        })
    }
  }
}
</script>
