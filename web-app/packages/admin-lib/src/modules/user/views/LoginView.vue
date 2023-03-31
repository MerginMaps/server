<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <login-view-template @userLogin="handleUserLogin" />
</template>

<script>
import { LoginViewTemplate } from '@mergin/lib'
import { mapActions } from 'vuex'

export default {
  name: 'LoginView',
  components: {
    LoginViewTemplate
  },
  methods: {
    ...mapActions('userModule', [
      'redirectAfterLogin',
      'redirectFromLoginAfterLogin'
    ]),
    ...mapActions('adminModule', ['adminLogin']),
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
}
</script>
