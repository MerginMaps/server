<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card>
    <v-card-title>
      <span class="text-h5">Change password</span>
    </v-card-title>
    <v-card-text>
      <v-form
        @submit.prevent
        class="layout column"
        cy-data="user-change-password-form"
      >
        <v-text-field
          label="Old Password"
          name="oldPassword"
          color="inputColor"
          v-model="oldPassword"
          cy-data="user-change-password-old"
          :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
          @click:append="passwordVisible = !passwordVisible"
          :type="passwordVisible ? 'text' : 'password'"
          :error-messages="errors.old_password"
        />
        <v-text-field
          label="New Password"
          name="password"
          color="inputColor"
          v-model="password"
          cy-data="user-change-password-new"
          :type="passwordVisible ? 'text' : 'password'"
          :error-messages="errors.password"
          @keyup.enter="changePassword"
        />
        <v-text-field
          label="Confirm New Password"
          name="confirm"
          color="inputColor"
          v-model="confirm"
          cy-data="user-change-password-confirm"
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
              <v-icon v-on="on" class="ml-1 mb-1" style="margin-right: 1rem"
                >info
              </v-icon>
            </template>
            <ul>
              <li>Password must be at least 8 characters long.</li>
              <li>
                Password must contain at least 3 character categories among the
                following:
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
          <v-spacer />
          <v-btn
            class="text--primary"
            @click="close"
            cy-data="user-change-password-close-btn"
          >
            Close
          </v-btn>
          <v-btn
            class="primary text--white"
            :disabled="!password || !oldPassword || !confirm"
            @click="changePassword"
            cy-data="user-change-password-change-btn"
          >
            Change
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { mapActions, mapGetters } from 'vuex'

import { waitCursor } from '@/common/html_utils'

export default defineComponent({
  data() {
    return {
      oldPassword: '',
      password: '',
      confirm: '',
      passwordVisible: false
    }
  },
  computed: {
    ...mapGetters('formModule', ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    }
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions('formModule', ['clearErrors']),
    ...mapActions('dialogModule', ['close']),
    ...mapActions('userModule', {
      changePasswordAction: 'changePassword'
    }),
    changePassword() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const data = {
        old_password: this.oldPassword,
        password: this.password,
        confirm: this.confirm
      }
      waitCursor(true)
      this.changePasswordAction({ data, componentId: this.merginComponentUuid })
    }
  }
})
</script>
