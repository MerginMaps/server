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
import { defineComponent } from 'vue'

import DashboardCoreAppBar from '../components/DashboardCoreAppBar.vue'
import DashboardCoreDrawer from '../components/DashboardCoreDrawer.vue'
import ServerNotConfigured from '../components/ServerNotConfigured.vue'

export default defineComponent({
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
:deep(.v-application--wrap) {
  overflow-y: auto;
}
</style>
