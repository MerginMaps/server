<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <dashboard-view-template :canCreateProject="canCreateProject">
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
      <!-- Projects -->
      <app-container>
        <app-section>
          <template #title>Recent active projects</template>
          <template #default>
            <projects-table-data-loader
              :show-namespace="false"
              :showFooter="false"
              :public="false"
              :initialOptions="initialOptions"
            />
          </template>
        </app-section>
      </app-container>
    </template>
  </dashboard-view-template>
</template>

<script lang="ts">
import {
  DashboardViewTemplate,
  ProjectsTableDataLoader,
  DashboardUsageInfoRow,
  DashboardFullStorageWarningRow,
  DashboardAccessRequestsRow,
  ProjectAccessRequestTable,
  FullStorageWarning,
  useUserStore,
  AppSection,
  AppContainer
} from '@mergin/lib'
import { defineComponent, computed, ref } from 'vue'

export default defineComponent({
  name: 'DashboardView',
  components: {
    DashboardViewTemplate,
    ProjectsTableDataLoader,
    DashboardAccessRequestsRow,
    DashboardFullStorageWarningRow,
    DashboardUsageInfoRow,
    ProjectAccessRequestTable,
    AppSection,
    FullStorageWarning,
    AppContainer
  },
  setup() {
    const initialOptions = ref({
      sortBy: 'updated',
      sortDesc: true,
      itemsPerPage: 5,
      page: 1
    })

    const userStore = useUserStore()

    const canCreateProject = computed(() => userStore.isGlobalWorkspaceAdmin)

    return {
      initialOptions,
      userStore,
      canCreateProject
    }
  }
})
</script>
