<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <slot v-if="usage > 90" :usage="usage" />
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'DashboardFullStorageWarningRow',
  computed: {
    ...mapState(useUserStore, ['currentWorkspace']),
    usage() {
      return Math.floor(
        (this.currentWorkspace?.disk_usage / this.currentWorkspace?.storage) *
          100
      )
    }
  },
})
</script>

<style scoped></style>
