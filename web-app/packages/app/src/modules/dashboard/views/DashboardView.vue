<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <dashboard-view-template :canCreateProject="canCreateProject">
    <template #usageInfo>
      <dashboard-usage-info-row />
    </template>
    <template #content>
      <dashboard-access-requests-row v-if="userStore.isGlobalWorkspaceAdmin">
        <template v-slot:table="{ namespace }">
          <project-access-request-table :namespace="namespace" />
        </template>
      </dashboard-access-requests-row>
      <dashboard-projects-row>
        <template #projects>
          <projects-table-data-loader
            :show-namespace="false"
            :showFooter="false"
            :showHeader="false"
            :sortable="false"
            :public="false"
            :initialOptions="initialOptions"
            show-tags
          />
        </template>
      </dashboard-projects-row>
    </template>
  </dashboard-view-template>
</template>

<script lang="ts">
import {
  DashboardViewTemplate,
  DashboardProjectsRow,
  DashboardAccessRequestsRow,
  ProjectsTableDataLoader,
  DashboardUsageInfoRow,
  ProjectAccessRequestTable,
  useProjectStore,
  useUserStore
} from '@mergin/lib'
import { defineComponent, computed, ref, onMounted } from 'vue'

export default defineComponent({
  name: 'DashboardView',
  components: {
    DashboardViewTemplate,
    DashboardProjectsRow,
    DashboardAccessRequestsRow,
    ProjectsTableDataLoader,
    DashboardUsageInfoRow,
    ProjectAccessRequestTable
  },
  setup() {
    const initialOptions = ref({
      sortBy: ['updated'],
      sortDesc: [true],
      itemsPerPage: 5,
      page: 1
    })

    const projectStore = useProjectStore()
    const userStore = useUserStore()

    const canCreateProject = computed(
      () => userStore.isGlobalWorkspaceAdmin?.value
    )

    onMounted(async () => {
      await projectStore.initProjects({
        params: { per_page: 5, page: 1 }
        // TODO: transform options to request params
        // params: initialOptions.value
      })
    })

    return {
      initialOptions,
      userStore,
      canCreateProject
    }
  }
})
</script>
