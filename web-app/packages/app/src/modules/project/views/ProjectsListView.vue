<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <projects-list-view-template
    :namespace="namespace"
    :can-create-project="canCreateProject"
  >
    <template #projects="{ onlyPublic }">
      <projects-table-data-loader
        :key="namespace + $route.name"
        :show-namespace="false"
        :namespace="namespace"
        :only-public="onlyPublic"
      />
    </template>
  </projects-list-view-template>
</template>

<script>
import { ProjectsListViewTemplate, ProjectsTableDataLoader } from '@mergin/lib'
import { computed } from '@vue/composition-api'
import { useGetters } from 'vuex-composition-helpers'

export default {
  name: 'ProjectsListView',
  components: {
    ProjectsListViewTemplate,
    ProjectsTableDataLoader
  },
  props: {
    namespace: String
  },
  setup() {
    const { isGlobalWorkspaceAdmin } = useGetters('userModule', [
      'isGlobalWorkspaceAdmin'
    ])
    const canCreateProject = computed(() => isGlobalWorkspaceAdmin?.value)
    return {
      canCreateProject
    }
  }
}
</script>
