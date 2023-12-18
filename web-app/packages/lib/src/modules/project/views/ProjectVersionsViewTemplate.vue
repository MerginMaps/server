<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section>
      <PDataView
        :value="items"
        :data-key="'name'"
        :paginator="
          showPagination && options && versionsCount > options.itemsPerPage
        "
        :rows="options.itemsPerPage"
        :totalRecords="versionsCount"
        :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
        data-cy="project-verision-table"
        lazy
        @page="onPage"
        :pt="{
          header: {
            // small header
            class: 'px-3 py-2'
          }
        }"
      >
        <template #header>
          <div class="w-11 grid grid-nogutter">
            <!-- Visible on lg breakpoint > -->
            <div
              v-for="col in columns.filter((item) => !item.fixed)"
              :class="['text-xs hidden lg:flex', `col-${col.cols ?? 1}`]"
              :key="col.text"
            >
              {{ col.text }}
            </div>
            <!-- else -->
            <div class="col-12 flex lg:hidden">Versions</div>
          </div>
        </template>

        <!-- table rows -->
        <template #list="slotProps">
          <div
            v-for="item in slotProps.items"
            :key="item.id"
            class="flex align-items-center hover:bg-gray-200 cursor-pointer border-bottom-1 border-gray-200 text-sm px-3 py-2 mt-0"
            :style="[rowStyle(item)]"
          >
            <div
              class="flex-grow-1 grid grid-nogutter w-11"
              @click.prevent="!item.disabled && rowClick(item.name)"
            >
              <!-- Columns, we are using data view instead table, it is better handling of respnsive state -->
              <template
                v-for="col in columns.filter((item) => !item.fixed)"
                :key="col.value"
              >
                <div
                  v-if="col.value === 'name'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">
                    {{ item.name }}
                  </span>
                </div>
                <div
                  v-else-if="col.value === 'created'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span
                    v-tooltip.bottom="{
                      value: $filters.datetime(item.created)
                    }"
                    :class="col.textClass"
                  >
                    {{ $filters.timediff(item.created) }}
                  </span>
                </div>
                <div
                  v-else-if="col.value === 'changes.added'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">{{
                    item.changes.added.length
                  }}</span>
                </div>
                <div
                  v-else-if="col.value === 'changes.updated'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">
                    {{ item.changes.updated.length }}
                  </span>
                </div>
                <div
                  v-else-if="col.value === 'changes.removed'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">
                    {{ item.changes.removed.length }}
                  </span>
                </div>
                <div
                  v-else-if="col.value === 'project_size'"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">{{
                    $filters.filesize(item.project_size)
                  }}</span>
                </div>
                <div
                  v-else
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 1}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">{{ item[col.value] }}</span>
                </div>
              </template>
            </div>
            <!-- actions -->
            <div class="flex w-1 flex-shrink-0 justify-content-end">
              <PButton
                icon="ti ti-download"
                severity="secondary"
                text
                :disabled="item.disabled"
                :style="[rowStyle(item)]"
                data-cy="project-versions-download-btn"
                @click="
                  downloadArchive({
                    url:
                      '/v1/project/download/' +
                      namespace +
                      '/' +
                      projectName +
                      '?version=' +
                      item.name +
                      '&format=zip'
                  })
                "
              />
            </div>
          </div>
        </template>
        <template #empty>
          <div class="w-full text-center p-4">
            <span>No versions found.</span>
          </div>
        </template>
      </PDataView>
      <slot name="table-footer"></slot>
    </app-section>
  </app-container>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { DataViewPageEvent } from 'primevue/dataview'
import { defineComponent, PropType } from 'vue'

import { AppSection, AppContainer } from '@/common/components'
import {
  FetchProjectVersionsParams,
  ProjectVersion,
  ProjectVersionsItem
} from '@/modules'
import { useProjectStore } from '@/modules/project/store'

interface ColumnItem {
  text: string
  value: string
  cols?: number
  fixed?: boolean
  textClass?: string
}

export default defineComponent({
  name: 'ProjectVersionsViewTemplate',
  components: {
    AppSection,
    AppContainer
  },
  props: {
    projectName: String,
    namespace: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
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
          textClass: 'font-semibold white-space-normal'
        },
        { text: 'Created', value: 'created', cols: 2 },
        { text: 'Author', value: 'author', cols: 2 },
        {
          text: 'Files added',
          value: 'changes.added',
          cols: 2
        },
        {
          text: 'Files edited',
          value: 'changes.updated',
          cols: 2
        },
        {
          text: 'Files removed',
          value: 'changes.removed',
          cols: 2
        },
        { text: 'Size', value: 'project_size' },
        { text: '', value: 'archived', fixed: true }
      ].map((item) => ({
        ...item,
        textClass: item.textClass === undefined ? 'opacity-80' : item.textClass
      })) as ColumnItem[],
      options: {
        sortDesc: [true],
        itemsPerPage: this.defaultItemsPerPage ?? 50,
        page: 1
      }
    }
  },
  computed: {
    ...mapState(useProjectStore, [
      'versions',
      'versionsLoading',
      'versionsCount'
    ]),
    /**
     * Table data from versions in global state transformed
     */
    items(): ProjectVersionsItem[] {
      const versions: ProjectVersion[] = this.versions

      return versions?.map<ProjectVersionsItem>((v) => ({
        ...v,
        disabled: this.disabledKeys.some((d) => d === v.name)
      }))
    }
  },
  created() {
    this.fetchVersions()
  },
  methods: {
    ...mapActions(useProjectStore, ['fetchProjectVersions', 'downloadArchive']),
    rowStyle(item: ProjectVersionsItem) {
      return item.disabled && { opacity: 0.5, cursor: 'not-allowed' }
    },
    async fetchVersions() {
      const params: FetchProjectVersionsParams = {
        page: this.options.page,
        per_page: this.options.itemsPerPage,
        descending: this.options.sortDesc[0]
      }
      await this.fetchProjectVersions({
        params,
        namespace: this.namespace,
        projectName: this.projectName
      })
    },
    onPage(e: DataViewPageEvent) {
      this.options.page = e.page + 1
      this.options.itemsPerPage = e.rows
      this.fetchVersions()
    },
    rowClick(name: string) {
      this.$router.push({
        path: `history/${name}`
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.p-dataview-content div {
  word-break: break-word;
}
</style>
