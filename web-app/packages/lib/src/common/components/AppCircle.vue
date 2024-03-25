<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div
    :class="[
      'flex align-items-center justify-content-center',
      'circle border-circle text-center text-color-forest',
      sizeClasses,
      severityClass
    ]"
  >
    <slot></slot>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props =
  defineProps<{ severity?: 'danger' | 'warn' | 'success'; size?: 'small' }>()

const severityClass = computed(
  () =>
    ({
      danger: 'circle--danger',
      warn: 'circle--warn',
      success: 'circle--success'
    }[props.severity])
)
const sizeClasses = computed(
  () =>
    ({ small: 'circle--small paragraph-p6 p-1' }[props.size] ||
    'w-2rem h-2rem paragraph-p4 p-2')
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
  &--small {
    width: 22px;
    height: 22px;
  }
}
</style>
