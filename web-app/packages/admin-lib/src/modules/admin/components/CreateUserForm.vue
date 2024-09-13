<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <form @submit.prevent="submit" class="flex flex-column pb-4">
    <span class="p-input-filled">
      <label for="username">First name</label>
      <PInputText
        id="username"
        v-model="username"
        data-cy="create-user-username"
        :class="['w-full', errors.username ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="username-error"
      />
      <span class="p-error paragraph-p6" id="username-error">{{
        errors.username?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <label for="email">Email</label>
      <PInputText
        id="email"
        v-model="email"
        data-cy="create-user-email"
        :class="['w-full', errors.email ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="email-error"
      />
      <span class="p-error paragraph-p6" id="email-error">{{
        errors.email?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <app-password-tooltip for="newPassword"
        ><template #label>Password</template>
      </app-password-tooltip>
      <PPassword
        id="newPassword"
        v-model="password"
        data-cy="change-password"
        :class="['w-full', errors.password ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="password-error"
        placeholder="Enter password"
      />
      <span class="p-error paragraph-p6" id="password-error">{{
        errors.password?.[0] || '&nbsp;'
      }}</span>
    </span>

    <!-- Footer -->
    <div
      class="w-full flex flex-column lg:flex-row justify-content-between align-items-center mt-4"
    >
      <PButton
        severity="secondary"
        @click="close"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        data-cy="profile-edit-close-btn"
        >Cancel</PButton
      >

      <PButton
        type="submit"
        class="flex w-12 lg:w-6 justify-content-center"
        data-cy="profile-edit-save-btn"
      >
        Create
      </PButton>
    </div>
  </form>
</template>

<script lang="ts">
import {
  errorUtils,
  htmlUtils,
  useDialogStore,
  useNotificationStore,
  useFormStore,
  AppPasswordTooltip
} from '@mergin/lib'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { AdminApi, CreateUserData } from '..'

export default defineComponent({
  components: {
    AppPasswordTooltip
  },
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
      const data: CreateUserData = {
        username: this.username.trim(),
        email: this.email.trim(),
        password: this.password,
        confirm: this.password
      }
      htmlUtils.waitCursor(true)
      this.clearErrors({ componentId: this.merginComponentUuid })
      AdminApi.createUser(data)
        .then(() => {
          this.close()
          this.$emit('success')
          this.show({
            text: 'User created'
          })
        })
        .catch((err) => {
          this.handleError({
            componentId: this.merginComponentUuid,
            error: err,
            generalMessage: errorUtils.getErrorMessage(
              err,
              'Failed to create user'
            )
          })
        })
        .finally(() => htmlUtils.waitCursor(false))
    }
  }
})
</script>

<style lang="scss" scoped></style>
