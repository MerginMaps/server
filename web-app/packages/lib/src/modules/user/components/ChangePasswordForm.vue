<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="flex flex-column p-4 row-gap-1">
    <span class="p-input-filled">
      <label for="oldPassowrd">Old password</label>
      <PPassword
        id="oldPassowrd"
        v-model="oldPassword"
        cy-data="user-change-password-old"
        :class="['w-full my-1', errors.old_password ? 'p-invalid' : '']"
        toggleMask
        :feedback="false"
        aria-describedby="old-password-error"
        placeholder="Please enter your password"
        :pt="{
          input: {
            root: { class: 'w-full border-round-xl' }
          }
        }"
      />
      <span class="p-error text-xs" id="old-password-error">{{
        errors.old_password?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <label class="flex align-items-center" for="newPassword"
        >New Password&nbsp;<i
          class="ti ti-info-circle-filled cursor-pointer text-color-medium-green hover:text-color text-base"
          v-tooltip="{
            value: passwordTooltip,
            escape: false
          }"
      /></label>

      <PPassword
        id="newPassword"
        v-model="password"
        :class="['w-full my-1', errors.password ? 'p-invalid' : '']"
        cy-data="user-change-password-new"
        aria-describedby="password-error"
        toggleMask
        :feedback="false"
        placeholder="Please enter your new password"
        :pt="{
          input: {
            root: { class: 'w-full border-round-xl' }
          }
        }"
      />
      <span class="p-error text-xs" id="password-error">{{
        errors.password?.[0] || '&nbsp;'
      }}</span>
    </span>

    <span class="p-input-filled">
      <label class="flex align-items-center" for="confirm"
        >Confirm password&nbsp;
        <i
          class="ti ti-info-circle-filled cursor-pointer text-color-medium-green hover:text-color text-base"
          :style="{ color: 'var(--medium-green-color)' }"
          v-tooltip="{
            value: passwordTooltip,
            escape: false
          }"
      /></label>

      <PPassword
        id="confirm"
        v-model="confirm"
        :class="['w-full my-1', errors.confirm ? 'p-invalid' : '']"
        cy-data="user-change-password-confirm"
        aria-describedby="confirm-password-error"
        toggleMask
        :feedback="false"
        placeholder="Please enter your new password"
        :pt="{
          input: {
            root: { class: 'w-full border-round-xl' }
          }
        }"
      />

      <span class="p-error text-xs" id="confirm-password-error">{{
        errors.confirm?.[0] || '&nbsp;'
      }}</span>
    </span>

    <!-- Footer -->
    <div
      class="w-full flex flex-column lg:flex-row justify-content-between align-items-center mt-4"
    >
      <PButton
        severity="secondary"
        outlined
        @click="close"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        cy-data="user-change-password-close-btn"
        >Cancel</PButton
      >

      <PButton
        :disabled="!password || !oldPassword || !confirm"
        @click="changePassword"
        class="flex w-12 lg:w-6 justify-content-center"
        cy-data="user-change-password-change-btn"
      >
        Save changes
      </PButton>
    </div>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { waitCursor } from '@/common/html_utils'
import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

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
    ...mapState(useFormStore, ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    },
    passwordTooltip() {
      return `
      <ul>
        <li>Password must be at least 8 characters long.</li>
        <li>Password must contain at least 3 character categories among the following:</li>
          Lowercase characters (a-z)
          Uppercase characters (A-Z)
          Digits (0-9)
          Special characters
      </ul>
      `
    }
  },
  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },
  methods: {
    ...mapActions(useFormStore, ['clearErrors']),
    ...mapActions(useDialogStore, ['close']),
    ...mapActions(useUserStore, {
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
