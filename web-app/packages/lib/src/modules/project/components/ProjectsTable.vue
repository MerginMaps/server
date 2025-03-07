<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <PDataTable
      v-if="numberOfItems > 0"
      :value="projects"
      :paginator="showFooter"
      :rows="modelValue?.itemsPerPage"
      :first="(modelValue?.page - 1) * (modelValue?.itemsPerPage ?? 1)"
      :totalRecords="numberOfItems"
      :loading="loading"
      :lazy="true"
      size="small"
      :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
      data-cy="project-table"
      @row-click="rowClick"
      @page="onPage"
    >
      <template v-for="col in columns" :key="col.field">
        <PColumn
          v-if="col.field === 'name'"
          :field="col.field"
          :header="col.header"
          style="width: 40%"
          class="pl-4"
        >
          <template #body="slotProps">
            <p class="title-t4">
              <router-link
                :to="{
                  name: 'project',
                  params: {
                    namespace: slotProps.data.namespace,
                    projectName: slotProps.data.name
                  }
                }"
              >
                <template v-if="showNamespace"
                  >{{ slotProps.data.namespace }} / </template
                >{{ slotProps.data.name }}</router-link
              ><PTag
                v-if="slotProps.data.access.public && !onlyPublic"
                severity="success"
                :pt="{ root: { class: 'ml-1' } }"
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
              <i
                v-if="slotProps.data.has_conflict"
                v-tooltip.right="{
                  value: 'Conflicting file in project'
                }"
                class="ti ti-alert-triangle-filled ml-1"
                style="margin-right: 20px"
                data-cy="project-form-conflict-file"
              ></i>
            </p>
            <span
              v-tooltip.right="{
                value: $filters.datetime(slotProps.data.updated),
                pt: { root: { 'data-cy': 'project-form-updated' } }
              }"
              class="opacity-80 m-0 paragraph-p7"
            >
              Updated {{ $filters.timediff(slotProps.data.updated) }}
            </span>
          </template>
        </PColumn>
        <PColumn
          v-else-if="col.field === 'version'"
          :field="col.field"
          :header="col.header"
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
        >
          <template #body="slotProps"
            ><span class="opacity-80" data-cy="project-form-project-size">{{
              slotProps.data.access.readers.length
            }}</span></template
          ></PColumn
        >

        <PColumn v-else :field="col.field" :header="col.header"></PColumn>
      </template>
    </PDataTable>
    <!-- Empty state -->
    <slot v-else name="empty"></slot>
  </div>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import { mapState } from 'pinia'
import { DataTablePageEvent, DataTableRowClickEvent } from 'primevue/datatable'
import { defineComponent, PropType } from 'vue'

import { useProjectStore } from '../store'

import { PaginatedGridOptions, TableDataHeader } from '@/common'
import { ProjectListItem } from '@/modules/project/types'

export default defineComponent({
  name: 'projects-table',
  props: {
    showNamespace: {
      type: Boolean,
      default: false
    },
    namespace: String,
    onlyPublic: {
      type: Boolean,
      default: true
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    modelValue: {
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
      loading: false
    }
  },
  computed: {
    ...mapState(useProjectStore, ['projectsSearch', 'projectsSorting']),
    columns(): TableDataHeader[] {
      return [
        { header: 'Project name', field: 'name' },
        { header: 'Versions', field: 'version' },
        { header: 'Size', field: 'meta.size' }
        // {
        //   header: 'Collaborators',
        //   field: 'access.readers'
        // }
      ]
    }
  },
  watch: {
    projectsSearch: {
      handler: debounce(function () {
        this.filterData()
      }, 500)
    },
    projectsSorting: {
      deep: true,
      handler() {
        this.fetchProjects()
      }
    }
  },
  created() {
    this.filterData()
  },
  methods: {
    fetchProjects() {
      this.loading = true
      this.$emit(
        'fetch-projects',
        {
          searchFilterByProjectName: this.projectsSearch,
          namespace: this.namespace
        },
        { ...this.projectsSorting },
        () => {
          this.loading = false
        }
      )
    },
    filterData() {
      this.$emit('update:modelValue', { ...this.modelValue, page: 1 })
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
    },
    onPage(e: DataTablePageEvent) {
      this.$emit('update:modelValue', {
        ...this.modelValue,
        page: e.page + 1,
        itemsPerPage: e.rows
      })
      this.fetchProjects()
    }
  }
})
</script>

<style lang="scss" scoped></style>
