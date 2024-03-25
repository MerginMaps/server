<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <projects-table
      v-bind="$props"
      v-model="options"
      :show-footer="showFooter && projectsCount > options.itemsPerPage"
      :projects="projects"
      :numberOfItems="projectsCount"
      @fetch-projects="fetchProjects"
    >
      <template #empty>
        <div class="flex flex-column align-items-center p-4 text-center">
          <img src="@/assets/map-circle.svg" alt="No projects" />
          <p class="title-t2 m-0 p-4">
            <template v-if="projectsSearch"
              >We couldn't find any projects matching your search
              criteria.</template
            >
            <template v-else>You don't have any projects yet.</template>
          </p>
          <template v-if="canCreateProject">
            <p class="paragraph-p6 opacity-80 pb-4">
              Let’s start by creating a first one!
            </p>
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
  data() {
    return {
      options: { ...this.initialOptions }
    }
  },
  computed: {
    ...mapState(useProjectStore, [
      'projects',
      'projectsCount',
      'projectsSearch'
    ])
  },
  methods: {
    ...mapActions(useProjectStore, ['getProjects']),
    ...mapActions(useNotificationStore, ['error']),
    ...mapActions(useDialogStore, ['show']),
    async fetchProjects(
      projectGridState: ProjectGridState,
      additionalGridOptions: PaginatedGridOptions,
      onFinish?: () => void
    ) {
      const params = {} as PaginatedProjectsParams
      const gridOptions = { ...this.options, ...additionalGridOptions }
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
      const dialog = { persistent: true, header: 'New project' }
      this.show({
        component: ProjectForm,
        params: {
          dialog,
          listeners: {
            error: (err, data) => this.$emit('new-project-error', err, data)
          }
        }
      })
    }
  }
})
</script>
