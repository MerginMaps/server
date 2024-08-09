<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container
    v-if="adminStore.displayUpdateAvailable && adminStore.info_url"
  >
    <app-section-banner>
      <template #title>Update available 🎉!</template>
      <template #description
        >A new version of Mergin Maps is available for users. Let's explore its
        new features.</template
      >
      <template #header-actions
        ><PButton
          @click="openUpdateUrl"
          severity="secondary"
          data-cy="check-for-updates-btn"
          label="Update"
      /></template>
    </app-section-banner>
  </app-container>
</template>

<script lang="ts" setup>
import { useInstanceStore, AppSectionBanner, AppContainer } from '@mergin/lib'

import { useAdminStore } from '@/modules/admin/store'

const instanceStore = useInstanceStore()
const adminStore = useAdminStore()

adminStore.getCheckUpdateFromCookies()
adminStore.checkVersions({
  major: instanceStore.configData?.major,
  minor: instanceStore.configData?.minor,
  fix: instanceStore.configData?.fix ?? null
})

function openUpdateUrl() {
  window.open(adminStore.info_url, '_blank')
}
</script>

<style scoped></style>
