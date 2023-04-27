<!--
Based on template:
Product Page: https://www.creative-tim.com/product/vuetify-material-dashboard
Copyright 2019 Creative Tim (https://www.creative-tim.com)

Modifications by:
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-app-bar id="app-bar" absolute app color="transparent" text height="75">
    <v-layout class="content">
      <v-btn
        class="mr-3 toggle-toolbar small-screen"
        elevation="1"
        fab
        small
        @click="setDrawer({ drawer: !drawer })"
      >
        <v-icon v-if="drawer" class="primary--text">
          fa-angle-double-left
        </v-icon>
        <v-icon v-else class="primary--text"> fa-angle-double-right</v-icon>
      </v-btn>
      <h3 class="align-self-center" v-if="displayUpdateAvailable && info_url">
        <a class="secondary--text" :href="info_url" target="_blank">
          Update available 🎉!
        </a>
      </h3>
      <v-spacer />

      <v-toolbar-title
        class="hidden-sm-and-down font-weight-light align-self-center"
        v-text="$route.name"
      />

      <v-spacer />

      <v-btn
        color="primary"
        class="mx-1 px-6 white--text"
        data-cy="drawer-btn-logout"
        id="logout-btn"
        @click="logout"
      >
        Log out
      </v-btn>
    </v-layout>
  </v-app-bar>
</template>

<script lang="ts">
import { UserApi } from '@mergin/lib'
import { defineComponent } from 'vue'
import { mapState, mapMutations, mapGetters, mapActions } from 'vuex'

export default defineComponent({
  name: 'DashboardCoreAppBar',

  props: {
    value: {
      type: Boolean,
      default: false
    }
  },

  data: () => ({
    notifications: []
  }),

  computed: {
    ...mapState('layoutModule', ['drawer']),
    ...mapState('instanceModule', ['configData']),
    ...mapState('adminModule', ['info_url']),
    ...mapGetters('adminModule', ['displayUpdateAvailable'])
  },

  methods: {
    ...mapMutations('layoutModule', ['setDrawer']),
    ...mapActions('adminModule', ['removeServerConfiguredCookies']),
    async logout() {
      try {
        await UserApi.logout()
        if (this.$route.path === '/') {
          location.reload()
        } else {
          location.href = '/'
        }
        await this.removeServerConfiguredCookies()
      } catch (e) {
        console.log(e)
      }
    }
  }
})
</script>

<style lang="scss" scoped>
@media (min-width: 960px) {
  .small-screen {
    display: none;
  }
}
</style>
