<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <settings-view-template>
    <app-settings-item v-for="item in settingsItems" :key="item.key">
      <template #title>{{ item.title }}</template>
      <template #description
        >{{ item.description
        }}<template v-if="item.key === 'usageInformation'">
          Click
          <a
            class="font-semibold text-color-forest"
            :href="instanceStore.configData?.docs_url"
            target="_blank"
            >here</a
          >
          for more information.</template
        ></template
      >
      <template #action>
        <div class="flex-shrink-0 paragraph-p1">
          <PInputSwitch
            :model-value="Boolean(instanceStore.configData?.collect_statistics)"
            disabled
          />
        </div>
      </template>
    </app-settings-item>
  </settings-view-template>
</template>

<script setup lang="ts">
import {
  AppSettingsItemConfig,
  useInstanceStore,
  AppSettingsItem
} from '@mergin/lib'
import { ref } from 'vue'

import SettingsViewTemplate from '@/modules/admin/views/SettingsViewTemplate.vue'

const instanceStore = useInstanceStore()

const settingsItems = ref<AppSettingsItemConfig[]>([
  {
    title: 'Collect statistics',
    description:
      'Help us improve Mergin Maps by sharing usage information. Mergin Maps collects anonymous usage information to make the service better overtime. You can opt-out anytime.',
    key: 'usageInformation'
  }
])
</script>

<style scoped></style>
