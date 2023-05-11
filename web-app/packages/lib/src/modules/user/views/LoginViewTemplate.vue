<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <custom-page class="login-window">
    <v-card>
      <mergin-logo-light @click="navigateHome" />
      <v-card-text>
        <v-form @submit.prevent class="login-form">
          <template v-if="forgotPassword">
            <v-text-field
              placeholder="Email"
              name="email"
              color="inputColor"
              data-cy="reset-form-email"
              v-model="email"
              :error-messages="errors.email"
              @keyup.enter="reset"
            />
            <v-btn
              :dark="email !== ''"
              color="secondary"
              data-cy="reset-form-btn"
              :disabled="!email"
              @click="reset"
            >
              Reset Password
            </v-btn>
          </template>
          <template v-else>
            <v-text-field
              placeholder="Username or email"
              data-cy="login-form-login"
              name="login"
              color="inputColor"
              v-model="login"
              :error-messages="errors.login"
              @keyup.enter="loginUser"
            />
            <v-text-field
              placeholder="Password"
              data-cy="login-form-password"
              name="password"
              color="inputColor"
              v-model="password"
              :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
              @click:append="passwordVisible = !passwordVisible"
              :type="passwordVisible ? 'text' : 'password'"
              :error-messages="errors.password"
              @keyup.enter="loginUser"
            />
            <v-btn
              :dark="Boolean(login && password)"
              :disabled="!login || !password"
              data-cy="login-form-btn-login"
              color="secondary"
              class="mx-0 mt-3"
              id="login-btn"
              @click="loginUser"
            >
              Sign In
            </v-btn>
          </template>
        </v-form>
        <div class="d-flex justify-space-between">
          <v-btn
            v-if="!forgotPassword"
            text
            small
            data-cy="login-form-btn-reset"
            color="primary"
            class="reset"
            :to="{ name: 'login', params: { reset: 'reset' } }"
            >Forgot password?
          </v-btn>
          <slot name="additionalButtons"></slot>
        </div>
      </v-card-text>
    </v-card>
  </custom-page>
</template>

<script lang="ts">
import { mapActions, mapGetters, mapState } from 'pinia'

import CustomPage from '@/common/components/CustomPage.vue'
import MerginLogoLight from '@/common/components/MerginLogoLight.vue'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

export default {
  name: 'LoginViewTemplate',
  components: { MerginLogoLight, CustomPage },
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
    ...mapGetters(useFormStore, ['getErrorByComponentId']),
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
  }
}
</script>

<style lang="scss" scoped>
.login-window {
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;

  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: auto;

  .bg {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 100%;
    object-fit: cover;
  }

  .container {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
  }

  :deep(.v-card) {
    min-width: 300px;
    max-width: 400px;
    flex: 1;

    .v-responsive__content {
      display: flex;
      flex-direction: row;
      justify-content: center;
      margin-left: 5px;
      cursor: pointer;

      img {
        height: 4em;
        width: auto;
      }
    }

    .v-card__text {
      display: flex;
      flex-direction: column;
    }

    form {
      display: flex;
      flex-direction: column;

      input {
        padding-left: 0.25em;
      }

      .input-group label:after {
        /* Remove asterisk from required fields */
        display: none;
      }

      .v-input__append-inner {
        .v-icon {
          color: #ccc !important;
        }
      }
    }

    .version {
      margin: 1em 0 0.5em 0;
      text-align: center;
      opacity: 0.6;
      font-size: 90%;
    }
  }

  .copyright {
    position: absolute;
    right: -1em;
    bottom: 0.25em;
    padding: 0 2em 0 2em;
    color: #fff;
    text-shadow: 1px 1px 3px #333;
    opacity: 0.7;
    user-select: none;

    b {
      font-weight: 500;
    }
  }

  :deep(.v-btn) {
    text-transform: none;

    &.reset {
      align-self: center;
    }
  }
}
</style>
