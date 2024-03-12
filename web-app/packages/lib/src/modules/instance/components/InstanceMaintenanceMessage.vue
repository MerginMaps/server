<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <PMessage severity="warn" :closable="false" class="m-0">
      <template #messageicon="slotProps">
        <i :class="[slotProps.class, 'ti ti-alert-triangle-filled']" />
      </template>
      <p>
        The service is currently in read-only mode for maintenance. Upload and
        update functions are not available at this time. Please try again later.
      </p></PMessage
    >
  </app-container>
</template>

<script setup lang="ts">
import { AppContainer } from '@/common/components'
</script>

<style scoped></style>
