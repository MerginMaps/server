<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PPanel v-bind="$props" toggleable :collapsed="collapsed" :pt="pt">
    <template v-if="$slots.header" #header>
      <slot name="header"></slot>
    </template>
    <template v-else-if="$slots.title" #header>
      <h3 class="text-color-forest font-semibold m-0 title-t3">
        <slot name="title"></slot>
      </h3>
    </template>
    <template v-if="$slots.footer" #footer>
      <slot name="footer"></slot>
    </template>
    <template #icons>
      <slot name="icons"></slot>
    </template>
    <slot></slot>
    <template #togglericon="{ collapsed }">
      <i
        :class="[
          'font-semibold text-color-forest ti',
          collapsed ? 'ti-chevron-down' : 'ti-chevron-up'
        ]"
        data-cy="collapse-btn"
      ></i>
    </template>
  </PPanel>
</template>

<script lang="ts" setup>
import { PanelProps } from 'primevue/panel'
import { ref, computed } from 'vue'

const props = defineProps<PanelProps>()
const collapsed = ref(props.collapsed)

const pt = computed(() => ({
  header: {
    class: [
      'surface-section border-none cursor-pointer',
      // Toggle border radius by open / closed panel
      collapsed.value ? 'border-round-2xl' : 'border-round-top-2xl',
      props.pt?.header?.class ?? 'p-4'
    ],
    onclick: headerClick
  },
  content: {
    class: 'border-none border-round-bottom-2xl p-4 pt-0'
  }
}))

function headerClick() {
  collapsed.value = !collapsed.value
}
</script>
