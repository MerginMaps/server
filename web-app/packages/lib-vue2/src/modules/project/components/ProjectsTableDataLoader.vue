<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <projects-table
    v-bind="$props"
    :projects="projects"
    :numberOfItems="numberOfItems"
    :onlyPublic="onlyPublic"
    @fetch-projects="fetchProjects"
  />
</template>

<script lang="ts">
import { mapActions } from 'pinia'
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
    sortable: {
      type: Boolean,
      default: true
    },
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
        sortBy: ['updated'],
        sortDesc: [true],
        itemsPerPage: 25,
        page: 1
      })
    }
  },
  data() {
    return {
      numberOfItems: 0,
      projects: []
    }
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
      if (gridOptions.sortBy[0]) {
        let orderParam = ''
        if (gridOptions.sortBy[0] === 'meta.size') {
          orderParam = 'disk_usage'
        } else {
          orderParam =
            gridOptions.sortBy[0] === 'owner'
              ? 'namespace'
              : gridOptions.sortBy[0]
        }
        params.order_params =
          orderParam + (gridOptions.sortDesc[0] ? '_desc' : '_asc')
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
        const response = await this.getProjects({ params })
        this.projects = response.data?.projects
        this.numberOfItems = response.data?.count
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
