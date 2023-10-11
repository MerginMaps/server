<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<!--  this is merely a placeholder for some custom warning to be added into page view -->
<template>
  <global-warning-template />
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import GlobalWarningTemplate from '@/common/components/GlobalWarningTemplate.vue'

export default defineComponent({
  name: 'GlobalWarning',
  components: { GlobalWarningTemplate }
})
</script>

<style scoped></style>
