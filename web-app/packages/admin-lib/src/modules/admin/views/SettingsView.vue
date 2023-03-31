<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <settings-view-template>
    <usage-information-card />
    <check-for-updates-card />
  </settings-view-template>
</template>

<script lang="ts">
import Vue from 'vue'

import CheckForUpdatesCard from '@/modules/admin/components/CheckForUpdatesCard.vue'
import UsageInformationCard from '@/modules/admin/components/UsageInformationCard.vue'
import SettingsViewTemplate from '@/modules/admin/views/SettingsViewTemplate.vue'

export default Vue.extend({
  name: 'SettingsView',
  components: {
    CheckForUpdatesCard,
    SettingsViewTemplate,
    UsageInformationCard
  }
})
</script>

<style scoped></style>
