<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <server-not-configured />
  <check-for-updates />
  <slot />
</template>

<script lang="ts" setup>
/** Consider if we want to support this */
import CheckForUpdates from './CheckForUpdates.vue'
import ServerNotConfigured from './ServerNotConfigured.vue'
</script>
<style lang="scss" scoped></style>
