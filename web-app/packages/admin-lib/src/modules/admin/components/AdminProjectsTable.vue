<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">Projects</h1>
        </template>
      </app-section>
    </app-container>
    <app-container>
      <app-section ground>
        <span class="p-input-icon-left w-full">
          <i class="ti ti-search paragraph-p3"></i>
          <PInputText
            :placeholder="
              showNamespace
                ? 'Search by workspace name or project name'
                : 'Search projects'
            "
            v-model="search"
            class="w-full"
            @input="onSearch"
          />
        </span>
      </app-section>
    </app-container>
    <app-container>
      <app-section>
        <PDataTable
          :value="projects.items"
          :lazy="true"
          :paginator="true"
          :rows="options.itemsPerPage"
          :rowsPerPageOptions="options.perPageOptions"
          :totalRecords="projects.count"
          :loading="projects.loading"
          :first="(options.page - 1) * options.itemsPerPage"
          :sortField="options.sortBy[0]"
          :sortOrder="options.sortDesc[0] ? -1 : 1"
          :rowHover="true"
          :row-class="(data) => (data.removed_at ? 'opacity-80' : '')"
          removableSort
          reorderable-columns
          @page="onPage"
          @sort="onSort"
          data-cy="projects-table"
        >
          <template v-for="header in headers" :key="header.field">
            <PColumn
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="{ data }">
                <router-link
                  v-if="
                    !header.conditionalLink || !data[header.conditionalLink]
                  "
                  :to="projectRoute(data)"
                  class="dt-row-link"
                  :class="header.class"
                >
                  <span
                    v-if="header.type === 'timediff'"
                    :title="$filters.datetime(data[header.field])"
                    >{{ $filters.timediff(data[header.field]) }}</span
                  >
                  <template v-else>{{ cellContent(data, header) }}</template>
                </router-link>
                <span v-else>
                  <span
                    v-if="header.type === 'timediff'"
                    :title="$filters.datetime(data[header.field])"
                    >{{ $filters.timediff(data[header.field]) }}</span
                  >
                  <template v-else>{{ cellContent(data, header) }}</template>
                </span>
              </template>
            </PColumn>
          </template>

          <PColumn
            field="removed_at"
            header="Scheduled removal at"
            :sortable="true"
          >
            <template #body="{ data }">
              <span
                :title="`Scheduled for removal at ${$filters.datetime(
                  data.removed_at
                )}`"
              >
                {{ $filters.timediff(data.removed_at) }}
              </span>
            </template>
          </PColumn>

          <PColumn field="removed_by" header="Removed by" :sortable="true">
            <template #body="{ data }">
              {{ data.removed_by }}
            </template>
          </PColumn>

          <PColumn>
            <template #body="{ data }">
              <div class="justify-center px-0" v-if="data.removed_at">
                <div class="flex align-items-center gap-1">
                  <PButton
                    label="Restore"
                    severity="secondary"
                    size="small"
                    @click="confirmRestore(data)"
                  />
                  <PButton
                    label="Delete"
                    severity="danger"
                    size="small"
                    @click="confirmDelete(data)"
                  />
                </div>
              </div>
            </template>
          </PColumn>

          <template #paginatorstart>
            <PButton
              icon="ti ti-refresh"
              plain
              text
              rounded
              size="small"
              @click="onRefresh"
            />
          </template>
          <template #paginatorend />
        </PDataTable>
      </app-section>
    </app-container>
  </div>
</template>

<script lang="ts">
import {
  ConfirmDialog,
  TableDataHeader,
  useDataTableSearch,
  useDialogStore,
  useNotificationStore,
  SortingOptions,
  AppSection,
  AppContainer,
  ConfirmDialogProps
} from '@mergin/lib'
import { mapState, mapActions } from 'pinia'
import { PropType, defineComponent } from 'vue'

import { AdminRoutes, useAdminStore } from '@/main'

export default defineComponent({
  name: 'projects-table',
  components: {
    AppContainer,
    AppSection
  },
  props: {
    showNamespace: Boolean,
    initialOptions: {
      type: Object as PropType<SortingOptions>,
      default: () => ({
        sortBy: ['updated'],
        sortDesc: [true],
        itemsPerPage: 20,
        page: 1,
        perPageOptions: [20, 50, 100]
      })
    }
  },
  setup(props) {
    const adminStore = useAdminStore()
    const dialogStore = useDialogStore()
    const notificationStore = useNotificationStore()

    const tableSearch = useDataTableSearch({
      defaultSortBy: props.initialOptions.sortBy[0],
      defaultSortDesc: props.initialOptions.sortDesc[0]
    })

    tableSearch.setFetchFn((signal) => {
      const { options, search } = tableSearch
      adminStore.getProjects({
        params: { ...options, like: search.value },
        signal
      })
    })

    return {
      ...tableSearch,
      showDialog: dialogStore.show.bind(dialogStore),
      error: notificationStore.error.bind(notificationStore),
      show: notificationStore.show.bind(notificationStore)
    }
  },
  computed: {
    ...mapState(useAdminStore, ['projects']),
    headers(): TableDataHeader[] {
      const cols: TableDataHeader[] = []
      if (this.showNamespace) {
        cols.push({
          field: 'workspace',
          header: 'Workspace',
          sortable: true,
          linked: true,
          conditionalLink: 'removed_at'
        })
      }
      cols.push(
        {
          field: 'name',
          header: 'Name',
          sortable: true,
          linked: true,
          class: 'font-semibold',
          conditionalLink: 'removed_at'
        },
        {
          field: 'updated',
          header: 'Last Update',
          sortable: true,
          linked: true,
          type: 'timediff',
          conditionalLink: 'removed_at'
        },
        {
          field: 'disk_usage',
          header: 'Size',
          sortable: true,
          linked: true,
          type: 'filesize',
          conditionalLink: 'removed_at'
        }
      )
      return cols
    }
  },
  created() {
    this.initFromQuery()
    this.doFetch()
  },
  methods: {
    ...mapActions(useAdminStore, ['restoreProject', 'deleteProject']),

    cellContent(
      data: Record<string, unknown>,
      header: TableDataHeader
    ): string {
      const val = data[header.field]
      if (header.type === 'timediff') return this.$filters.timediff(val)
      if (header.type === 'filesize') return this.$filters.filesize(val, 'MB')
      return String(val ?? '')
    },

    projectRoute(data) {
      return {
        name: AdminRoutes.PROJECT,
        params: { namespace: data.workspace, projectName: data.name }
      }
    },

    confirmRestore(item) {
      const props: ConfirmDialogProps = {
        text: `Are you sure to restore project ${item.workspace}/${item.name}?`,
        confirmText: 'Restore'
      }
      const listeners = {
        confirm: async () => {
          await this.restoreProject({ projectId: item.id })
          this.doFetch()
        }
      }
      this.showDialog({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { header: 'Restore project' } }
      })
    },

    confirmDelete(item) {
      const props: ConfirmDialogProps = {
        text: `Are you sure you want to permanently delete this project?`,
        description: `Deleting this project will remove it
      and all its data. This action cannot be undone. Type in project name to confirm:`,
        hint: item.name,
        confirmText: 'Delete permanently',
        confirmField: {
          label: 'Project name',
          expected: item.name
        },
        severity: 'danger'
      }
      const listeners = {
        confirm: async () => {
          await this.deleteProject({ projectId: item.id })
          this.doFetch()
        }
      }
      this.showDialog({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { header: 'Delete project' } }
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
