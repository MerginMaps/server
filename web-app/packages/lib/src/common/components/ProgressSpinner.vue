<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-progress-circular class="mx-2" :size="22" :width="3" indeterminate />
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'ProgressSpinner'
})
</script>

<style scoped></style>
