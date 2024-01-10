<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Padding equals 20px -->
  <div class="app-container mx-auto pt-3 pb-1 px-4 xl:px-0">
    <slot></slot>
  </div>
</template>

<script lang="ts" setup></script>

<style scoped lang="scss">
.app-container {
  // From figma design
  max-width: 1120px;
}
</style>
