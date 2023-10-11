<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <usage-status />
    <dashboard-full-storage-warning-row v-slot="{ usage, username }">
      <full-storage-warning :usage="usage" :username="username" />
    </dashboard-full-storage-warning-row>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import FullStorageWarning from '@/common/components/FullStorageWarning.vue'
import UsageStatus from '@/common/components/UsageStatus.vue'
import DashboardFullStorageWarningRow from '@/modules/dashboard/components/DashboardFullStorageWarningRow.vue'

export default defineComponent({
  name: 'DashboardUsageInfoRow',
  components: {
    DashboardFullStorageWarningRow,
    FullStorageWarning,
    UsageStatus
  }
})
</script>

<style scoped></style>
