<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-onboarding-page>
    <template #header>
      <h1 class="text-6xl">
        <template v-if="forgotPassword">Reset password</template
        ><template v-else>Sign in</template>
      </h1>
    </template>

    <!-- Passing slots to aother components -->
    <template v-if="$slots.aside" #aside><slot name="aside"></slot></template>
    <template v-if="$slots.logo" #logo><slot name="logo"></slot></template>

    <form
      v-if="forgotPassword"
      @submit.prevent="reset"
      class="flex flex-column row-gap-1"
    >
      <div>
        <label class="text-xs" for="login">Email</label>
        <PInputText
          placeholder="Type your email"
          name="email"
          color="inputColor"
          data-cy="reset-form-email"
          v-model="email"
          :class="['w-full my-1', errors.email ? 'p-invalid' : '']"
        />
        <span class="p-error text-xs" id="login-error">{{
          errors.email?.[0] || '&nbsp;'
        }}</span>
      </div>

      <router-link
        class="text-sm text-color-forest font-semibold align-self-center"
        :to="{ name: 'login' }"
        >Back to login</router-link
      >

      <PButton
        class="mt-6"
        data-cy="reset-form-btn"
        :disabled="!email"
        @click="reset"
        label="Reset password"
      />
    </form>
    <form v-else @submit.prevent="loginUser" class="flex flex-column row-gap-1">
      <div>
        <label class="text-xs" for="login">Username or email</label>
        <PInputText
          id="login"
          name="login"
          v-model="login"
          data-cy="login-form-login"
          :class="['w-full my-1', errors.login ? 'p-invalid' : '']"
          aria-describedby="login-error"
          placeholder="Please enter username or email"
          :inputProps="{ autocomplete: 'on' }"
          autofocus
        />
        <span class="p-error text-xs" id="login-error">{{
          errors.login?.[0] || '&nbsp;'
        }}</span>
      </div>

      <div>
        <label class="text-xs" for="password">Password</label>
        <PPassword
          id="password"
          name="password"
          v-model="password"
          :class="['w-full my-1', errors.password ? 'p-invalid' : '']"
          data-cy="login-form-password"
          aria-describedby="password-error"
          toggleMask
          :feedback="false"
          placeholder="Please enter your password"
          :pt="{
            input: {
              root: {
                class: 'w-full border-round-xl',
                autocomplete: 'current-password'
              }
            }
          }"
        />
        <span class="p-error text-xs" id="password-error">{{
          errors.password?.[0] || '&nbsp;'
        }}</span>
      </div>

      <router-link
        class="text-sm text-color-forest font-semibold align-self-center"
        :to="{ name: 'login', params: { reset: 'reset' } }"
        >Forgot password?</router-link
      >

      <PButton
        type="submit"
        :disabled="!login || !password"
        data-cy="login-form-btn-login"
        id="login-btn"
        class="mt-6 w-full"
        label="Sign in"
      />
    </form>
    <div class="flex flex-column align-items-center">
      <slot name="additionalButtons"> </slot>
    </div>
  </app-onboarding-page>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'

import AppOnboardingPage from '@/common/components/AppOnboardingPage.vue'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

export default {
  name: 'LoginViewTemplate',
  props: {
    presetLogin: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      valid: true,
      login: this.presetLogin ?? '',
      password: '',
      email: '',
      passwordVisible: false
    }
  },
  created() {
    if (this.presetLogin) {
      this.login = this.presetLogin
    }
    this.updateLoggedUser({ loggedUser: null }) // clear current user to prevent commit to store (and thus reload)
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useFormStore, ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    },
    forgotPassword() {
      return this.$route.params.reset === 'reset'
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
    ...mapActions(useUserStore, [
      'updateLoggedUser',
      'userLogin',
      'resetPassword'
    ]),
    loginUser() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      const data = {
        login: this.login.trim(),
        password: this.password.trim()
      }
      this.$emit('userLogin', {
        data,
        currentRoute: this.$route,
        componentId: this.merginComponentUuid
      })
    },
    reset() {
      this.clearErrors({ componentId: this.merginComponentUuid })
      this.resetPassword({
        email: this.email,
        componentId: this.merginComponentUuid
      })
    },
    navigateHome() {
      this.$router.push('/')
    }
  },
  components: { AppOnboardingPage }
}
</script>

<style lang="scss" scoped></style>
