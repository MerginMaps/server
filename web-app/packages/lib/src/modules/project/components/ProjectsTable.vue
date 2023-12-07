<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <PDataTable
      :value="projects"
      :paginator="showFooter"
      :first="options.page - 1"
      :rows="options.itemsPerPage"
      :rowsPerPageOptions="[10, 25, 50, 100]"
      :currentPage="options.page"
      :totalRecords="numberOfItems"
      :loading="loading"
      :lazy="true"
      size="small"
      @row-click="rowClick"
    >
      <template v-for="col in columns" :key="col.field">
        <PColumn
          v-if="col.field === 'name'"
          :field="col.field"
          :header="col.header"
          style="width: 40%"
          class="pl-4"
          :pt="ptColumn"
        >
          <template #body="slotProps">
            <p class="font-semibold text-sm">
              {{ slotProps.data.name
              }}<PTag
                v-if="slotProps.data.access.public"
                severity="success"
                :pt="{ root: { class: 'p-1 ml-1' } }"
                >Public</PTag
              >
              <i
                v-if="!slotProps.data.tags.includes('valid_qgis')"
                v-tooltip.right="{
                  value: 'Failed to find a QGIS project file'
                }"
                class="ti ti-alert-circle-filled ml-1"
                data-cy="project-form-missing-project"
                style="color: var(--grape-color)"
              ></i>
            </p>
            <p
              v-tooltip.bottom="{
                value: $filters.datetime(slotProps.data.updated),
                pt: { root: { 'data-cy': 'project-form-updated' } }
              }"
              class="text-color-secondary text-xs"
            >
              Updated {{ $filters.timediff(slotProps.data.updated) }}
            </p>
          </template>
        </PColumn>
        <PColumn
          v-else-if="col.field === 'version'"
          :field="col.field"
          :header="col.header"
          :pt="ptColumn"
        >
          <template #body="slotProps"
            ><span class="opacity-80" data-cy="project-form-history">{{
              slotProps.data.version.substr(1)
            }}</span></template
          ></PColumn
        >
        <PColumn
          v-else-if="col.field === 'meta.size'"
          :field="col.field"
          :header="col.header"
          :pt="ptColumn"
        >
          <template #body="slotProps"
            ><span class="opacity-80" data-cy="project-form-project-size">{{
              $filters.filesize(slotProps.data.disk_usage, 'MB', 1)
            }}</span></template
          ></PColumn
        >
        <PColumn
          v-else-if="col.field === 'access.readers'"
          :field="col.field"
          :header="col.header"
          style="width: 15%"
          :pt="ptColumn"
        >
          <template #body="slotProps"
            ><span class="opacity-80" data-cy="project-form-project-size">{{
              slotProps.data.access.readers.length
            }}</span></template
          ></PColumn
        >

        <PColumn
          v-else
          :field="col.field"
          :header="col.header"
          :pt="ptColumn"
        ></PColumn>
      </template>
      <template #empty>No projects found</template>
    </PDataTable>
  </div>
</template>

<script lang="ts">
import { DataTableRowClickEvent } from 'primevue/datatable'
import { defineComponent, PropType } from 'vue'

import { PaginatedGridOptions } from '@/common'
import { formatToTitle } from '@/common/text_utils'
import { ProjectListItem, TableDataHeader } from '@/modules/project/types'

export default defineComponent({
  name: 'projects-table',
  props: {
    showNamespace: {
      type: Boolean,
      default: false
    },
    namespace: String,
    showFooter: {
      type: Boolean,
      default: true
    },
    initialOptions: {
      type: Object as PropType<PaginatedGridOptions>
    },
    numberOfItems: {
      type: Number,
      default: 0
    },
    projects: Array as PropType<Array<ProjectListItem>>
  },
  data() {
    return {
      options: { ...this.initialOptions },
      searchFilterByProjectName: '',
      searchFilterByNamespace: '',
      searchFilterByDay: '',
      loading: false,
      keys: ['name', 'updated', 'disk_usage']
    }
  },
  computed: {
    columns(): TableDataHeader[] {
      let columns = []
      if (this.showNamespace) {
        columns.push({
          header: 'Workspace',
          field: 'namespace'
        })
      }
      columns = columns.concat(
        { header: 'Project name', field: 'name' },
        { header: 'Versions', field: 'version' },
        { header: 'Size', field: 'meta.size' },
        {
          header: 'Collaborators',
          field: 'access.readers'
        }
      )
      return columns
    },
    selectKeys() {
      return this.keys.map((i) => {
        return { title: formatToTitle(i), value: i }
      })
    },
    ptColumn() {
      return {
        headerCell: {
          style: {
            backgroundColor: '#F8F9FA'
          }
        },
        headerTitle: {
          class: 'text-xs'
        }
      }
    }
  },
  watch: {
    $route: {
      immediate: false,
      handler: 'changedRoute'
    }
  },
  created() {
    this.filterData()
  },
  methods: {
    paginating(options: PaginatedGridOptions) {
      this.options = options
    },
    fetchPage(page: number) {
      this.options.page = page
      this.fetchProjects()
    },
    changedRoute() {
      this.options.page = 1
      this.fetchProjects()
    },
    fetchProjects() {
      this.loading = true
      this.$emit(
        'fetch-projects',
        {
          searchFilterByProjectName: this.searchFilterByProjectName,
          searchFilterByNamespace: this.searchFilterByNamespace,
          namespace: this.namespace,
          searchFilterByDay: this.searchFilterByDay
        },
        this.options,
        () => {
          this.loading = false
        }
      )
    },
    filterData() {
      this.options.page = 1
      this.fetchProjects()
    },
    rowClick(e: DataTableRowClickEvent) {
      const { data } = e
      this.$router.push({
        name: 'project',
        params: {
          namespace: data.namespace,
          projectName: data.name
        }
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
