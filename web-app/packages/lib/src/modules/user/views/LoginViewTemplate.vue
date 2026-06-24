<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-onboarding-page>
    <template #header>
      <h1 class="headline-h1">
        <template v-if="forgotPassword">{{ t('ResetPassword') }}</template
        ><template v-else>{{ t('SignIn') }}</template>
      </h1>
    </template>

    <!-- Passing slots to another components -->
    <template v-if="$slots.aside" #aside><slot name="aside"></slot></template>
    <template v-if="$slots.logo" #logo><slot name="logo"></slot></template>

    <form
      v-if="forgotPassword"
      @submit.prevent="reset"
      class="flex flex-column"
    >
      <div>
        <label for="login">{{ t('Email') }}</label>
        <PInputText
          :placeholder="t('TypeYourEmail')"
          name="email"
          color="inputColor"
          data-cy="reset-form-email"
          v-model="email"
          :class="['w-full', errors.email ? 'p-invalid' : '']"
        />
        <span class="p-error paragraph-p6" id="login-error">{{
          errors.email?.[0] || '&nbsp;'
        }}</span>
      </div>

      <router-link
        class="text-color-forest align-self-center font-semibold"
        :to="{ name: 'login' }"
        >{{ t('BackToLogin') }}</router-link
      >

      <PButton
        class="mt-6"
        data-cy="reset-form-btn"
        :disabled="!email"
        @click="reset"
        :label="t('ResetPassword')"
      />
    </form>
    <form v-else @submit.prevent="loginUser" class="flex flex-column">
      <div>
        <label for="login">{{ t('UsernameOrEmail') }}</label>
        <PInputText
          id="login"
          name="login"
          v-model="login"
          data-cy="login-form-login"
          :class="['w-full', errors.login ? 'p-invalid' : '']"
          aria-describedby="login-error"
          :placeholder="t('PleaseEnterUsernameOrEmail')"
          :inputProps="{ autocomplete: 'on' }"
          autofocus
        />
        <span class="p-error paragraph-p6" id="login-error">{{
          errors.login?.[0] || '&nbsp;'
        }}</span>
      </div>

      <div>
        <label for="password">{{ t('Password') }}</label>
        <PPassword
          id="password"
          name="password"
          v-model="password"
          :class="['w-full', errors.password ? 'p-invalid' : '']"
          data-cy="login-form-password"
          aria-describedby="password-error"
          toggleMask
          :feedback="false"
          :prompt-label="t('EnterPassword')"
          :placeholder="t('PleaseEnterYourPassword')"
          :pt="{
            input: {
              root: {
                class: 'w-full border-round-xl',
                autocomplete: 'current-password'
              }
            }
          }"
        />
        <span class="p-error paragraph-p6" id="password-error">{{
          errors.password?.[0] || '&nbsp;'
        }}</span>
      </div>

      <router-link
        class="text-color-forest title-t3 align-self-center"
        :to="{ name: 'login', params: { reset: 'reset' } }"
        >{{ t('ForgotPassword') }}</router-link
      >

      <PButton
        type="submit"
        :disabled="!login || !password"
        data-cy="login-form-btn-login"
        id="login-btn"
        class="mt-6 w-full"
        size="large"
        :label="t('SignIn')"
      />
    </form>
    <div class="flex flex-column align-items-center">
      <slot name="additionalButtons"> </slot>
    </div>
  </app-onboarding-page>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'

import returnTranslation from '@/../../lang/translate'
import AppOnboardingPage from '@/common/components/AppOnboardingPage.vue'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

export default {
  name: 'LoginViewTemplate',
  setup() {
    return { t }
  },
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
  beforeUnmount() {
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
