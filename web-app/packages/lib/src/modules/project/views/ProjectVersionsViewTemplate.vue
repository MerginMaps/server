<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section ground class="flex justify-content-end">
      <AppMenu :items="filterMenuItems" />
    </app-section>
    <app-section>
      <DataViewWrapper
        lazy
        :rows="options.itemsPerPage"
        :totalRecords="versionsCount"
        :columns="columns"
        :value="items"
        :data-key="'name'"
        :options="options"
        :loading="versionsLoading"
        :row-style="rowStyle"
        @update:options="updateOptions"
        @row-click="rowClick"
        :paginator="
          showPagination && options && versionsCount > options.itemsPerPage
        "
        data-cy="project-version-table"
        :empty-message="'No versions found.'"
      >
        <template #header-title>Versions</template>

        <template #actions="{ item }">
          <PButton
            icon="ti ti-download"
            rounded
            plain
            text
            :disabled="item.disabled"
            :style="[rowStyle(item)]"
            class="paragraph-p3"
            data-cy="project-versions-download-btn"
            @click.stop="downloadClick(item)"
          />
        </template>

        <template #col-created="{ column, item }">
          <span
            v-tooltip.left="{
              value: $filters.datetime(item.created)
            }"
            :class="column.textClass"
          >
            {{ $filters.timediff(item.created) }}
          </span>
        </template>
        <template #col-project_size="{ item, column }">
          <span :class="column.textClass">{{
            $filters.filesize(item.project_size)
          }}</span>
        </template>
        <template #col-changes.added="{ item, column }">
          <span :class="column.textClass">{{ item.changes.added }}</span>
        </template>
        <template #col-changes.updated="{ item, column }">
          <span :class="column.textClass">{{
            item.changes.updated + item.changes.updated_diff
          }}</span>
        </template>
        <template #col-changes.removed="{ item, column }">
          <span :class="column.textClass">{{ item.changes.removed }}</span>
        </template>
      </DataViewWrapper>
      <slot name="table-footer"></slot>
    </app-section>
    <VersionDetailSidebar />
  </app-container>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { defineComponent, PropType, StyleValue } from 'vue'

import VersionDetailSidebar from '../components/VersionDetailSidebar.vue'

import { AppSection, AppContainer } from '@/common/components'
import AppMenu from '@/common/components/AppMenu.vue'
import DataViewWrapper from '@/common/components/data-view/DataViewWrapper.vue'
import {
  DataViewWrapperColumnItem,
  DataViewWrapperOptions
} from '@/common/components/data-view/types'
import { FetchProjectVersionsParams, ProjectVersionsTableItem } from '@/modules'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'ProjectVersionsViewTemplate',
  components: {
    AppSection,
    AppContainer,
    VersionDetailSidebar,
    AppMenu,
    DataViewWrapper
  },
  props: {
    projectName: String,
    namespace: String,
    /** Default items per page */
    defaultItemsPerPage: Number as PropType<number>,
    /** Disabled keys (name attribute of rows in vuetify table are keys for items) */
    disabledKeys: { type: Array as PropType<string[]>, default: () => [] },
    /** Show pagination */
    showPagination: { type: Boolean, default: true }
  },
  data() {
    return {
      columns: [
        {
          text: 'Version',
          value: 'name',
          textClass: 'font-semibold white-space-normal',
          cols: 1
        },
        { text: 'Created', value: 'created' },
        { text: 'Author', value: 'author' },
        {
          text: 'Files added',
          value: 'changes.added'
        },
        {
          text: 'Files edited',
          value: 'changes.updated'
        },
        {
          text: 'Files removed',
          value: 'changes.removed'
        },
        { text: 'Size', value: 'project_size', cols: 1 },
        { text: '', value: 'archived', fixed: true }
      ] as DataViewWrapperColumnItem[],
      options: {
        sortDesc: true,
        itemsPerPage: this.defaultItemsPerPage ?? 50,
        page: 1
      } as DataViewWrapperOptions
    }
  },
  computed: {
    ...mapState(useProjectStore, [
      'versions',
      'versionsLoading',
      'versionsCount',
      'project'
    ]),
    /**
     * Table data from versions in global state transformed
     */
    items(): ProjectVersionsTableItem[] {
      return this.versions?.map<ProjectVersionsTableItem>((v) => ({
        ...v,
        disabled: this.disabledKeys.some((d) => d === v.name)
      }))
    },
    filterMenuItems(): MenuItem[] {
      return [
        {
          label: 'Newest versions',
          key: 'newest',
          sortDesc: true
        },
        {
          label: 'Oldest versions',
          key: 'oldest',
          sortDesc: false
        }
      ].map((item) => ({
        ...item,
        command: (e: MenuItemCommandEvent) => this.menuItemClick(e),
        class: this.options.sortDesc === item.sortDesc ? 'bg-primary-400' : ''
      }))
    }
  },
  created() {
    this.fetchVersions()
  },
  methods: {
    ...mapActions(useProjectStore, ['getProjectVersions', 'downloadArchive']),
    rowStyle(item: ProjectVersionsTableItem): StyleValue {
      return (
        item.disabled && ({ opacity: 0.5, cursor: 'not-allowed' } as StyleValue)
      )
    },
    async fetchVersions() {
      const params: FetchProjectVersionsParams = {
        page: this.options.page,
        per_page: this.options.itemsPerPage,
        descending: this.options.sortDesc
      }
      await this.getProjectVersions({
        params,
        projectId: this.project?.id
      })
    },
    rowClick(item) {
      this.$router.push({
        path: `history/${item.name}`
      })
    },
    menuItemClick(e: MenuItemCommandEvent) {
      this.options.sortDesc = e.item.sortDesc
      this.fetchVersions()
    },
    async updateOptions(options: DataViewWrapperOptions) {
      this.options = options
      this.fetchVersions()
    },
    downloadClick(item) {
      this.downloadArchive({
        url:
          '/v1/project/download/' +
          this.namespace +
          '/' +
          this.projectName +
          '?version=' +
          item.name +
          '&format=zip'
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
