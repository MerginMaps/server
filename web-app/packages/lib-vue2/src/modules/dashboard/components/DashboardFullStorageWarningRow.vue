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
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'DashboardFullStorageWarningRow',
  computed: {
    ...mapState(useUserStore, ['loggedUser']),

    usage() {
      return Math.floor(
        (this.loggedUser?.disk_usage / this.loggedUser?.storage) * 100
      )
    }
  }
})
</script>

<style scoped></style>
