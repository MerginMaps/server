<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <dashboard-view-template>
    <template #usageInfo>
      <dashboard-usage-info-row />
      <dashboard-full-storage-warning-row v-slot="{ usage }">
        <full-storage-warning :usage="usage" />
      </dashboard-full-storage-warning-row>
    </template>
    <template #content>
      <dashboard-access-requests-row v-if="userStore.isGlobalWorkspaceAdmin">
        <template v-slot:table="{ namespace }">
          <project-access-request-table :namespace="namespace" />
        </template>
      </dashboard-access-requests-row>
      <dashboard-projects-row :canCreateProject="canCreateProject" />
    </template>
  </dashboard-view-template>
</template>

<script lang="ts">
import {
  DashboardViewTemplate,
  DashboardUsageInfoRow,
  DashboardFullStorageWarningRow,
  DashboardAccessRequestsRow,
  ProjectAccessRequestTable,
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
    DashboardFullStorageWarningRow,
    DashboardUsageInfoRow,
    ProjectAccessRequestTable,
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
