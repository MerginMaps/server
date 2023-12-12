<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <FullStorageWarningTemplate :usage="usage"></FullStorageWarningTemplate>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import FullStorageWarningTemplate from './FullStorageWarningTemplate.vue'

export default defineComponent({
  name: 'FullStorageWarning',
  components: { FullStorageWarningTemplate },
  props: {
    usage: Number
  }
})
</script>

<style scoped></style>
