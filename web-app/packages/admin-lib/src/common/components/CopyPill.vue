<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <button
    type="button"
    class="copy-pill"
    v-tooltip.top="'Copy to clipboard'"
    :aria-label="ariaLabel"
    :disabled="!value"
    @click="copyValue"
  >
    <span>{{ value }}</span>
    <i class="ti ti-copy"></i>
  </button>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@mergin/lib'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** Value shown in the pill and copied to the clipboard */
    value: string | number | null | undefined
    /** Human readable name of the value, used in notification and aria label */
    label?: string
  }>(),
  { label: 'Value' }
)

const notificationStore = useNotificationStore()

const ariaLabel = computed(() => `Copy ${props.label} ${props.value ?? ''}`)

async function copyValue() {
  if (props.value === null || props.value === undefined || props.value === '') {
    return
  }
  try {
    await navigator.clipboard.writeText(String(props.value))
    notificationStore.show({ text: `${props.label} copied to clipboard` })
  } catch {
    notificationStore.error({
      text: `Failed to copy ${props.label.toLowerCase()} to clipboard`
    })
  }
}
</script>

<style lang="scss" scoped>
.copy-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin: -0.25rem -0.5rem;
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-color);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;

  &:hover {
    background: var(--surface-hover);
  }

  &:disabled {
    cursor: default;
    opacity: 0.6;

    &:hover {
      background: transparent;
    }
  }

  i {
    font-size: 0.95rem;
    color: inherit;
  }
}
</style>
