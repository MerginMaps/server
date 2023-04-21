<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <projects-list-view-template
    :namespace="namespace"
    :can-create-project="canCreateProject"
    @new-project-error="onNewProjectError"
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
    const { handleError } = useActions('formModule', ['handleError'])
    
    const canCreateProject = computed(() => isGlobalWorkspaceAdmin?.value)

    /**
     * Error handler for create new project from $emit in Template
     * */
    function onNewProjectError(err, data) {
      handleError({
        componentId: data.componentId,
        error: err,
        generalMessage: 'Failed to create project.'
      })
    }

    return {
      canCreateProject,
      onNewProjectError
    }
  }
}
</script>
