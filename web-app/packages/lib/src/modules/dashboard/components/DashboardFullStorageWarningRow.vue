<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-row v-if="usage > 90">
    <slot :usage="usage" :username="loggedUser.username" />
  </v-row>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapState } from 'vuex'

export default Vue.extend({
  name: 'DashboardFullStorageWarningRow',
  computed: {
    ...mapState('userModule', ['loggedUser']),

    usage() {
      return Math.floor(
        (this.loggedUser?.disk_usage / this.loggedUser?.storage) * 100
      )
    }
  }
})
</script>

<style scoped></style>
