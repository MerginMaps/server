<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PToast position="top-center" :pt="{ content: 'align-items-center' }"
    >>
    <template #message="{ message }">
      <i :class="['p-toast-message-icon', icon(message.severity)]" />
      <div class="p-toast-message-text" data-pc-section="text">
        <span class="p-toast-summary" data-pc-section="summary">{{
          message.summary
        }}</span>
        <div
          v-if="message.detail"
          class="p-toast-detail text-color"
          data-pc-section="detail"
        >
          {{ message.detail }}
        </div>
      </div>
    </template>
  </PToast>
</template>

<script setup lang="ts">
import { ToastMessageOptions } from 'primevue/toast'

const icon = (severity: ToastMessageOptions['severity']) => {
  const mapper: Record<ToastMessageOptions['severity'], string> = {
    success: 'ti ti-circle-check-filled',
    info: 'ti ti-info-circle-filled',
    warn: 'ti ti-alert-circle-filled',
    error: 'ti ti-alert-circle-filled'
  }

  return mapper[severity] || 'ti ti-alert-circle-filled'
}
</script>
