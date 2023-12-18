<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <PButton
      severity="secondary"
      text
      :icon="icon"
      @click="toggleMenu"
      aria-haspopup="true"
      aria-controls="app-menu"
      class="text-2xl"
    />
    <PMenu ref="menu" id="app-menu" :model="items" :popup="true" />
  </div>
</template>

<script setup lang="ts">
import { MenuItem } from 'primevue/menuitem'
import { ref } from 'vue'

withDefaults(
  defineProps<{
    items: MenuItem[]
    icon: string
  }>(),
  { icon: 'ti ti-sort-descending' }
)

const menu = ref<{ toggle: (event: Event) => void }>()

function toggleMenu(event) {
  menu.value.toggle(event)
}
</script>
