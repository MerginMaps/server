<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<!--  this is merely a placeholder -->
<template>
  <div>
    <slot name="billing"></slot>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'UsageStatusTemplate'
})
</script>

<style scoped></style>
