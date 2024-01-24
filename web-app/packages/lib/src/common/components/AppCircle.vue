<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div
    :class="[
      'circle border-circle p-2 w-2rem h-2rem text-center text-color-forest text-base',
      severityClass
    ]"
  >
    <slot></slot>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';

const props = defineProps<{ severity?: 'danger' | 'warn' | 'success' }>()

const severityClass = computed(
  () =>
    ({
      danger: 'circle--danger',
      warn: 'circle--warn',
      success: 'circle--success'
    }[props.severity])
)
</script>

<style scoped lang="scss">
.circle {
  background-color: var(--light-green-color);
  &--danger {
    background-color: var(--negative-color);
  }
  &--warn {
    background-color: var(--warning-color);
  }
  &--success {
    background-color: var(--positive-color);
  }
}
</style>
