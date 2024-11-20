<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <article>
    <server-not-configured />
    <slot />
  </article>
</template>

<script lang="ts" setup>
/** Consider if we want to support this */
import ServerNotConfigured from './ServerNotConfigured.vue'
</script>
<style lang="scss" scoped></style>
