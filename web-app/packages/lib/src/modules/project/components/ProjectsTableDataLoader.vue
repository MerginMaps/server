<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <projects-table
    v-bind="$props"
    :projects="projects"
    :numberOfItems="projectsCount"
    :onlyPublic="onlyPublic"
    @fetch-projects="fetchProjects"
  />
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent, PropType } from 'vue'

import { PaginatedGridOptions } from '@/common'
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
    }
  },
  computed: {
    ...mapState(useProjectStore, ['projects', 'projectsCount'])
  },
  methods: {
    ...mapActions(useProjectStore, ['getProjects']),
    ...mapActions(useNotificationStore, ['error']),
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
        params.flag = this.$route.meta.flag
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
    }
  }
})
</script>
