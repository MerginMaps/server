<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-app>
    <dashboard-core-app-bar />

    <dashboard-core-drawer />

    <v-main>
      <server-not-configured />
      <slot />
      <!--      <router-view />-->
    </v-main>
  </v-app>
</template>

<script lang="ts">
import Vue from 'vue'

import DashboardCoreAppBar from '../components/DashboardCoreAppBar.vue'
import DashboardCoreDrawer from '../components/DashboardCoreDrawer.vue'
import ServerNotConfigured from '../components/ServerNotConfigured.vue'

export default Vue.extend({
  name: 'AdminLayoutView',

  components: {
    DashboardCoreAppBar,
    DashboardCoreDrawer,
    ServerNotConfigured
  },

  data: () => ({
    expandOnHover: false
  })
})
</script>
<style lang="scss" scoped>
::v-deep .v-application--wrap {
  overflow-y: auto;
}
</style>
