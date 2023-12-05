<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <usage-status />
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import UsageStatus from '@/common/components/UsageStatus.vue'

export default defineComponent({
  name: 'DashboardUsageInfoRow',
  components: {
    UsageStatus
  }
})
</script>

<style scoped></style>
