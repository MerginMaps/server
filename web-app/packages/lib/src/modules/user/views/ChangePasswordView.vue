<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <custom-page>
    <v-card
      style="min-width: 300px"
      class="text-center"
      v-on:="changePasswordWithToken"
    >
      <v-card-title class="justify-center text-primary font-weight-bold ml-3">
        <h3>Change password</h3>
      </v-card-title>
      <v-card-text>
        <v-form @submit.prevent v-if="!success" class="layout column">
          <v-text-field
            label="New Password"
            name="password"
            color="inputColor"
            v-model="password"
            data-cy="change-password"
            :append-icon="passwordVisible ? 'visibility_off' : 'visibility'"
            @click:append-inner="passwordVisible = !passwordVisible"
            :type="passwordVisible ? 'text' : 'password'"
            :error-messages="errors.password"
            v-on="on"
          >
            <template v-slot:append-outer>
              <v-tooltip
                location="top"
                color="orange"
                max-width="350"
                content-class="form-tooltip"
              >
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" class="ml-1 mb-1">info</v-icon>
                </template>
                <ul>
                  <li>Password must be at least 8 characters long.</li>
                  <li>
                    Password must contain at least 3 character categories among
                    the following:
                    <ul>
                      <li>Lowercase characters (a-z)</li>
                      <li>Uppercase characters (A-Z)</li>
                      <li>Digits (0-9)</li>
                      <li>Special characters</li>
                    </ul>
                  </li>
                </ul>
              </v-tooltip>
            </template>
          </v-text-field>
          <v-text-field
            label="Confirm New Password"
            name="confirm"
            color="inputColor"
            v-model="confirm"
            data-cy="change-password-confirm"
            :type="passwordVisible ? 'text' : 'password'"
            :error-messages="errors.confirm"
            @keyup.enter="changePasswordWithToken"
          />

          <v-card-actions class="justify-center">
            <v-btn
              class="bg-primary text-white"
              data-cy="change-password-btn"
              :disabled="!password || !confirm"
              @click="changePasswordWithToken"
            >
              Change
            </v-btn>
          </v-card-actions>
        </v-form>
        <div v-else>
          <p>Your password was changed. You can now Sign In</p>
          <v-btn
            class="align-self-center orange white--text"
            data-cy="change-password-btn-signin"
            href="/login"
            >Sign in
          </v-btn>
        </div>
        <br />
      </v-card-text>
    </v-card>
  </custom-page>
</template>

<script lang="ts">
import { mapActions, mapGetters } from 'pinia'
import { defineComponent } from 'vue'

import CustomPage from '@/common/components/CustomPage.vue'
import { useFormStore } from '@/modules/form/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ChangePasswordView',
  components: { CustomPage },
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
    ...mapGetters(useFormStore, ['getErrorByComponentId']),
    errors() {
      return this.getErrorByComponentId(this.merginComponentUuid) ?? {}
    },
    token() {
      return this.$route.params.token
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
.main-window {
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
}
</style>
