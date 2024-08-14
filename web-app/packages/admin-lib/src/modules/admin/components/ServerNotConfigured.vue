<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container v-if="displayBanner">
    <app-section-banner>
      <template #title> Server is not properly configured</template>
      <template #description
        >Your server is not configured properly for use in the production
        environment. Read more in the
        <a :href="docsLinkDocumentation" target="_blank">documentation</a> how
        to properly set up the deployment.</template
      >
      <template #header-actions
        ><PButton
          @click="dismiss"
          severity="secondary"
          data-cy="dismiss-server-configured-btn"
          label="Dismiss"
      /></template>
    </app-section-banner>
  </app-container>
</template>

<script lang="ts" setup>
import { useInstanceStore, AppSectionBanner, AppContainer } from '@mergin/lib'
import { computed } from 'vue'

import { useAdminStore } from '@/modules/admin/store'

const adminStore = useAdminStore()
const instanceStore = useInstanceStore()

const docsLinkDocumentation = computed(
  () => `${instanceStore.configData?.docs_url ?? ''}/dev/mergince`
)
const displayBanner = computed(
  () =>
    !instanceStore.configData?.server_configured &&
    !adminStore.isServerConfigHidden
)

function dismiss() {
  adminStore.setServerConfiguredCookies()
}

adminStore.getServerConfiguredCookies()
</script>

<style lang="scss" scoped></style>
