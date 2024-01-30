<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container v-if="open">
    <section>
      <PMessage severity="warn" @close="open = false">
        <template #messageicon="slotProps">
          <i :class="[slotProps.class, 'ti ti-alert-triangle-filled']" />
        </template>
        <p>
          The service is currently in read-only mode for maintenance. Upload and
          update functions are not available at this time. Please try again
          later.
        </p></PMessage
      >
    </section>
  </app-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { AppContainer } from '@/common/components'

/** Handle open state with connection to message close button */
const open = ref(true)
</script>

<style scoped></style>
