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
      <dashboard-access-requests-row v-if="isGlobalWorkspaceAdmin" />
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

<script>
import {
  DashboardViewTemplate,
  DashboardProjectsRow,
  DashboardAccessRequestsRow,
  ProjectsTableDataLoader,
  DashboardUsageInfoRow
} from '@mergin/lib'
import { computed, ref, onMounted } from '@vue/composition-api'
import { useActions, useGetters } from 'vuex-composition-helpers'

export default {
  name: 'DashboardView',
  components: {
    DashboardViewTemplate,
    DashboardProjectsRow,
    DashboardAccessRequestsRow,
    ProjectsTableDataLoader,
    DashboardUsageInfoRow
  },
  setup() {
    const initialOptions = ref({
      sortBy: ['updated'],
      sortDesc: [true],
      itemsPerPage: 5,
      page: 1
    })

    const { initProjects } = useActions('projectModule', ['initProjects'])
    const { isGlobalWorkspaceAdmin } = useGetters('userModule', [
      'isGlobalWorkspaceAdmin'
    ])
    const canCreateProject = computed(() => isGlobalWorkspaceAdmin?.value)

    onMounted(async () => {
      await initProjects({
        params: { per_page: 5, page: 1 }
        // TODO: transform options to request params
        // params: initialOptions.value
      })
    })

    return {
      initialOptions,
      isGlobalWorkspaceAdmin,
      canCreateProject
    }
  }
}
</script>
