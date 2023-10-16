<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<!--  this is merely a placeholder -->
<template>
  <UsageStatusTemplate></UsageStatusTemplate>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import UsageStatusTemplate from './UsageStatusTemplate.vue'

export default defineComponent({
  name: 'UsageStatus',
  components: { UsageStatusTemplate }
})
</script>

<style scoped></style>
