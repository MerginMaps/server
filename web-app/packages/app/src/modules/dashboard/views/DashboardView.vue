<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <dashboard-view-template>
    <full-storage-warning />
    <dashboard-access-requests-row v-if="userStore.isGlobalWorkspaceAdmin">
      <template v-slot:table="{ namespace }">
        <access-request-table :namespace="namespace" />
      </template>
    </dashboard-access-requests-row>
    <dashboard-projects-row :canCreateProject="canCreateProject" />
  </dashboard-view-template>
</template>

<script lang="ts">
import {
  DashboardViewTemplate,
  DashboardUsageInfoRow,
  DashboardAccessRequestsRow,
  AccessRequestTable,
  FullStorageWarning,
  useUserStore,
  DashboardProjectsRow
} from '@mergin/lib'
import { defineComponent, computed } from 'vue'

export default defineComponent({
  name: 'DashboardView',
  components: {
    DashboardViewTemplate,
    DashboardAccessRequestsRow,
    DashboardUsageInfoRow,
    AccessRequestTable,
    FullStorageWarning,
    DashboardProjectsRow
  },
  setup() {
    const userStore = useUserStore()

    const canCreateProject = computed(() => userStore.isGlobalWorkspaceAdmin)

    return {
      userStore,
      canCreateProject
    }
  }
})
</script>
