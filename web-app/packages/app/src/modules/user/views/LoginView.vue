<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <login-view-template @userLogin="handleUserLogin" />
</template>

<script lang="ts">
import { LoginViewTemplate, useUserStore } from '@mergin/lib'
import { mapActions } from 'pinia'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'LoginView',
  components: {
    LoginViewTemplate
  },
  methods: {
    ...mapActions(useUserStore, [
      'userLogin',
      'redirectAfterLogin',
      'redirectFromLoginAfterLogin'
    ]),
    async handleUserLogin(payload) {
      try {
        await this.userLogin(payload)
        if (payload.currentRoute.query.redirect) {
          await this.redirectAfterLogin({
            currentRoute: payload.currentRoute
          })
        } else {
          await this.redirectFromLoginAfterLogin({
            currentRoute: payload.currentRoute
          })
        }
      } catch(err) {
        console.error(err)
      }
    }
  }
})
</script>
