<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container v-if="open">
    <app-section ground>
      <PMessage severity="warn" @close="open = false">
        <template #messageicon="slotProps">
          <i :class="[slotProps.class, 'ti ti-alert-triangle-filled']" />
        </template>
        <p>
          <span class="font-semibold"
            >Your storage is almost full ({{ usage }}%).</span
          >
          Soon you will not be able to sync your projects.
          <slot name="buttons"></slot></p
      ></PMessage>
    </app-section>
  </app-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { AppContainer, AppSection } from '@/common/components'
import { useUserStore } from '@/main'

const userStore = useUserStore()

const usage = computed(() =>
  Math.floor(
    (userStore.currentWorkspace?.disk_usage /
      userStore.currentWorkspace?.storage) *
      100
  )
)

/** Handle open state with connection to message close button */
const isOver = computed({
  get() {
    return usage.value > 90
  },
  set(value) {
    open.value = value
  }
})
const open = ref(isOver)
</script>

<style scoped></style>
