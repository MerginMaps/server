<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container
    v-if="
      userStore.currentWorkspace &&
      projectStore.accessRequests &&
      projectStore.accessRequestsCount > 0
    "
  >
    <app-section>
      <template #title
        >Requests
        <span class="text-color-medium-green"
          >({{ projectStore.accessRequestsCount }})</span
        ></template
      >
      <template #default>
        <slot name="table" :namespace="userStore.currentWorkspace.name"></slot>
      </template>
    </app-section>
  </app-container>
</template>

<script lang="ts" setup>
import { AppContainer, AppSection } from '@/common/components'
import { useUserStore } from '@/main'
import { useProjectStore } from '@/modules/project/store'

const projectStore = useProjectStore()
const userStore = useUserStore()

if (userStore.currentWorkspace) {
  projectStore.initNamespaceAccessRequests({
    namespace: userStore.currentWorkspace.name,
    params: null
  })
}
</script>
