<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-form @submit.prevent ref="form">
    <v-card v-on:keyup.enter="submit" v-on:keyup.esc="close">
      <v-card-title>
        <span class="text-h5">
          <span>Create user</span>
        </span>
      </v-card-title>
      <v-card-text>
        <v-text-field
          placeholder="Username"
          name="username"
          color="inputColor"
          v-model="username"
          :error-messages="errors.username"
        />
        <v-text-field
          placeholder="Email"
          name="email"
          color="inputColor"
          v-model="email"
          :error-messages="errors.email"
        />
        <v-layout align-center>
          <v-text-field
            placeholder="Password"
            name="password"
            color="inputColor"
            v-model="password"
            :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
            @click:append="passwordVisible = !passwordVisible"
            :type="passwordVisible ? 'text' : 'password'"
            :error-messages="errors.password"
          />
          <v-tooltip
            top
            color="orange"
            max-width="350"
            content-class="form-tooltip"
          >
            <template v-slot:activator="{ on }">
              <v-icon v-on="on" class="ml-1 mb-1">info</v-icon>
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
        <slot />

        <v-card-actions>
          <v-spacer />
          <v-btn class="black--text" @click="close"> Close</v-btn>
          <v-btn
            class="orange white--text"
            :disabled="invalidInput"
            @click="submit"
          >
            Submit
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </v-form>
</template>

<script lang="ts">
import {
  postRetryCond,
  htmlUtils,
  useDialogStore,
  useNotificationStore,
  useFormStore
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

export default defineComponent({
  data() {
    return {
      isValid: null,
      username: '',
      email: '',
      password: '',
      passwordVisible: false
    }
  },
  computed: {
    ...mapState(useFormStore, ['getErrorByComponentId']),

    invalidInput() {
      return this.isValid === null
        ? this.validateInput(this.$data)
        : !this.isValid
    },
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
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useNotificationStore, ['show']),
    ...mapActions(useFormStore, ['clearErrors', 'handleError']),

    validateInput(data) {
      return ['username', 'email', 'password'].some((k) => data[k] === '')
    },
    submit() {
      const data = {
        username: this.username.trim(),
        email: this.email.trim(),
        password: this.password,
        confirm: this.password
      }
      htmlUtils.waitCursor(true)
      this.clearErrors({ componentId: this.merginComponentUuid })
      // TODO: JM - move to user api (and store action)
      this.$http
        .post('/app/auth/user', data, {
          'axios-retry': {
            retries: 5,
            retryCondition: (error) => postRetryCond(error)
          }
        })
        .then(() => {
          this.close()
          this.$emit('success')
          this.show({
            text: 'User created'
          })
        })
        .catch((err) => {
          const msg =
            err.response.data && err.response.data.detail
              ? err.response.data.detail
              : 'Failed to create user'
          this.handleError({
            componentId: this.merginComponentUuid,
            error: err,
            generalMessage: msg
          })
        })
        .finally(() => htmlUtils.waitCursor(false))
    }
  }
})
</script>

<style lang="scss" scoped>
.v-tooltip {
  cursor: default;
}
</style>

<style lang="scss">
.form-tooltip {
  opacity: 0.95 !important;

  ul {
    padding-left: 1em;
  }
}
</style>
