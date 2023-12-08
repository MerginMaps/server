<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <projects-table
      v-bind="$props"
      :projects="projects"
      :numberOfItems="projectsCount"
      @fetch-projects="fetchProjects"
    >
      <template #empty>
        <div class="flex flex-column align-items-center p-4 text-center">
          <img src="@/assets/map-circle.svg" alt="No projects" />
          <p class="font-semibold p-4">There are currently no projects.</p>
          <p class="text-sm opacity-80 m-0">
            You don’t have got any projects yet.
          </p>
          <template v-if="canCreateProject">
            <p class="text-sm opacity-80 pb-4">Please create new project.</p>
            <PButton @click="newProjectDialog">Create new project</PButton>
          </template>
        </div>
      </template>
    </projects-table>
  </div>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent, PropType } from 'vue'

import { PaginatedGridOptions } from '@/common'
import { ProjectForm, useDialogStore } from '@/modules'
import { useNotificationStore } from '@/modules/notification/store'
import ProjectsTable from '@/modules/project/components/ProjectsTable.vue'
import { useProjectStore } from '@/modules/project/store'
import {
  PaginatedProjectsParams,
  ProjectGridState
} from '@/modules/project/types'

export default defineComponent({
  name: 'projects-table-data-loader',
  components: { ProjectsTable },
  props: {
    showNamespace: Boolean,
    onlyPublic: {
      type: Boolean,
      default: false
    },
    namespace: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
    public: {
      type: Boolean,
      default: true
    },
    showHeader: {
      type: Boolean,
      default: true
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    initialOptions: {
      type: Object as PropType<PaginatedGridOptions>,
      default: () => ({
        itemsPerPage: 25,
        page: 1
      })
    },
    /** Whether the user can create a new project */
    canCreateProject: {
      type: Boolean as PropType<boolean>
    }
  },
  computed: {
    ...mapState(useProjectStore, ['projects', 'projectsCount'])
  },
  methods: {
    ...mapActions(useProjectStore, ['getProjects']),
    ...mapActions(useNotificationStore, ['error']),
    ...mapActions(useDialogStore, ['show']),
    async fetchProjects(
      projectGridState: ProjectGridState,
      gridOptions: PaginatedGridOptions,
      onFinish?: () => void
    ) {
      const params = {} as PaginatedProjectsParams
      if (
        this.$route.name === 'shared_projects' ||
        this.$route.name === 'my_projects'
      ) {
        params.flag = this.$route.meta.flag as string
      }
      params.page = gridOptions.page
      params.per_page = gridOptions.itemsPerPage
      if (gridOptions.sortBy) {
        let orderParam = ''
        if (gridOptions.sortBy === 'meta.size') {
          orderParam = 'disk_usage'
        } else {
          orderParam =
            gridOptions.sortBy === 'owner' ? 'namespace' : gridOptions.sortBy
        }
        params.order_params =
          orderParam + (gridOptions.sortDesc ? '_desc' : '_asc')
      }
      if (projectGridState.searchFilterByProjectName) {
        params.name = projectGridState.searchFilterByProjectName.trim()
      }
      if (projectGridState.searchFilterByNamespace) {
        params.namespace = projectGridState.searchFilterByNamespace.trim()
      }
      if (projectGridState.namespace) {
        params.only_namespace = projectGridState.namespace
      }
      if (this.asAdmin) {
        params.as_admin = true
      }
      if (!this.public) {
        params.public = false
      }
      if (this.onlyPublic) {
        params.only_public = true
      }
      if (
        projectGridState.searchFilterByDay &&
        projectGridState.searchFilterByDay >= 0
      ) {
        params.last_updated_in = projectGridState.searchFilterByDay
      }
      try {
        await this.getProjects({ params })
        if (onFinish) {
          onFinish()
        }
      } catch {
        if (onFinish) {
          onFinish()
        }
        await this.error({ text: 'Failed to fetch list of projects' })
      }
    },
    newProjectDialog() {
      const dialog = { maxWidth: 500, persistent: true }
      this.show({
        component: ProjectForm,
        params: {
          dialog
        }
      })
    }
  }
})
</script>
