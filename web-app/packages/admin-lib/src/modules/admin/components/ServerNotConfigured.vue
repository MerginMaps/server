<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container v-if="displayBanner">
    <app-section-banner>
      <template #title>{{ $t('ServerIsNotProperlyConfigured') }}</template>
      <template #description
        >{{
          $t(
            'YourServerIsNotConfiguredProperlyForUseInTheProductionEnvironmentReadMoreInThe'
          )
        }}
        <a :href="docsLinkDocumentation" target="_blank">{{
          $t('Documentation')
        }}</a>
        {{ $t('HowToProperlySetUpTheDeployment') }}.</template
      >
      <template #header-actions
        ><PButton
          @click="dismiss"
          severity="secondary"
          data-cy="dismiss-server-configured-btn"
          :label="$t('Dismiss')"
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
