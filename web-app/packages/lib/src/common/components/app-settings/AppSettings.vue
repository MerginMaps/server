<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->
<template>
  <div class="flex flex-column row-gap-3 px-4 pb-4">
    <slot name="items-start"></slot>
    <app-settings-item v-for="(item, index) in items" :key="index">
      <template #title>{{ item.title }}</template>
      <template #description>{{ item.description }}</template>
      <template #action>
        <slot :name="item.key" :item="item"></slot>
      </template>
    </app-settings-item>
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

import AppSettingsItem from './AppSettingsItem.vue'
import { AppSettingsItemConfig } from './types'

withDefaults(
  defineProps<{
    items?: AppSettingsItemConfig[]
  }>(),
  {
    items: () => []
  }
)
</script>
