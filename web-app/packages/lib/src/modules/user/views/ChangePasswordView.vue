<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <article
    class="relative change-password-view flex align-items-center justify-content-center h-full"
  >
    <aside class="absolute top-0 left-0 m-4">
      <img src="@/assets/mm-logo.svg" />
    </aside>
    <div
      class="change-password-view-container flex flex-column row-gap-4 p-4 lg:p-0"
    >
      <header class="align-self-center">
        <h1 class="text-6xl">Change password</h1>
      </header>
      <form
        v-if="!success"
        @submit.prevent="changePasswordWithToken"
        class="flex flex-column row-gap-1"
      >
        <span>
          <app-password-tooltip for="newPassword"
            ><template #label>New Password</template>
          </app-password-tooltip>
          <PPassword
            id="newPassword"
            v-model="password"
            data-cy="change-password"
            :class="['w-full my-1', errors.old_password ? 'p-invalid' : '']"
            toggleMask
            :feedback="false"
            aria-describedby="password-error"
            placeholder="Please enter your password"
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

        <span>
          <app-password-tooltip for="confirm">
            <template #label>Confirm password</template>
          </app-password-tooltip>

          <PPassword
            id="confirm"
            v-model="confirm"
            :class="['w-full my-1', errors.confirm ? 'p-invalid' : '']"
            data-cy="change-password-confirm"
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

        <PButton
          type="submit"
          class="mt-6"
          data-cy="change-password-btn"
          :disabled="!password || !confirm"
          label="Change"
        />
      </form>
      <div v-else class="flex flex-column align-items-center">
        <span
          >Your password was changed. You can now
          <router-link
            class="text-sm text-color-forest font-semibold align-self-center"
            :to="{ name: 'login' }"
            >Sign in</router-link
          ></span
        >
      </div>
    </div>
  </article>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import AppPasswordTooltip from '@/common/components/AppPasswordTooltip.vue'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ChangePasswordView',
  components: { AppPasswordTooltip },
  data() {
    return {
      on: '',
      success: false,
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
    token() {
      return this.$route.params.token as string
    }
  },

  beforeDestroy() {
    this.clearErrors({
      componentId: this.merginComponentUuid,
      keepNotification: true
    })
  },

  methods: {
    ...mapActions(useUserStore, {
      changePasswordWithTokenAction: 'changePasswordWithToken'
    }),
    ...mapActions(useFormStore, ['clearErrors', 'handleError']),
    responseCallback(value) {
      this.success = value
    },
    changePasswordWithToken() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const data = {
        password: this.password,
        confirm: this.confirm
      }

      this.changePasswordWithTokenAction({
        data,
        token: this.token,
        callback: this.responseCallback,
        componentId: this.merginComponentUuid
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.change-password-view {
  &-container {
    max-width: 480px;
    width: 100%;
  }
}
</style>
