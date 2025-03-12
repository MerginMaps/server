<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Tip from MM -->
  <div
    class="tip-message flex flex-column md:flex-row align-items-center border-round-xl p-4"
    :class="[severityClass]"
  >
    <slot name="image">
      <img
        v-if="severity === 'info'"
        width="50"
        height="50"
        src="@/assets/bulb.svg"
        aria-label="Bulb"
      />
      <img
        v-if="severity === 'danger'"
        width="50"
        height="50"
        src="@/assets/exclamation.svg"
        aria-label="Exclamation"
      />
    </slot>

    <div class="md:pl-4 text-center md:text-left">
      <p :class="['tip-message-title title-t3']">
        <slot name="title">Tip from Mergin Maps</slot>
      </p>
      <p class="opacity-80 paragraph-p6">
        <slot name="description"></slot>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { TipMessageProps } from './types'

type Severity = 'info' | 'danger'

const props = withDefaults(defineProps<TipMessageProps>(), {
  severity: 'info'
})

const severityClass = computed(() => {
  const mapper: Record<Severity, string> = {
    info: 'tip-message-info',
    danger: 'tip-message-danger'
  }
  return mapper[props.severity]
})
</script>

<style scoped lang="scss">
.tip-message {
  &.tip-message-info {
    background-color: var(--light-green-color);
    .tip-message-title {
      color: var(--deep-ocean-color);
    }
  }

  &.tip-message-danger {
    background-color: var(--negative-light-color);
    .tip-message-title {
      color: var(--grape-color);
    }
  }
}
</style>
