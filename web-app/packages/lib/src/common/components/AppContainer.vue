<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Padding equals 20px -->
  <div class="app-container mx-auto pt-3 pb-1">
    <slot></slot>
  </div>
</template>

<script lang="ts" setup></script>

<style scoped lang="scss">
.app-container {
  // From figma design + padding
  max-width: 1150px;
  padding-left: 15px;
  padding-right: 15px;
}
</style>
