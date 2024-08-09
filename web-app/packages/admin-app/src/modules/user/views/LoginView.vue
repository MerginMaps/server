<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <login-view-template @userLogin="handleUserLogin" />
</template>

<script lang="ts">
import { useAdminStore } from '@mergin/admin-lib'
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
      'redirectAfterLogin',
      'redirectFromLoginAfterLogin'
    ]),
    ...mapActions(useAdminStore, ['adminLogin']),
    async handleUserLogin(payload) {
      try {
        await this.adminLogin(payload)
        if (payload.currentRoute.query.redirect) {
          await this.redirectAfterLogin({
            currentRoute: payload.currentRoute
          })
        } else {
          await this.redirectFromLoginAfterLogin({
            currentRoute: payload.currentRoute
          })
        }
      } catch {}
    }
  }
})
</script>
