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
          removableSort
          reorderable-columns
          @page="onPage"
          @sort="onSort"
          @row-click="rowClick"
          data-cy="projects-table"
          :row-class="(data) => (data.removed_at ? 'opacity-80' : '')"
        >
          <template v-for="header in headers" :key="header.field">
            <PColumn
              v-if="showNamespace && header.field === 'workspace'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                {{ slotProps.data.workspace }}
              </template>
            </PColumn>

            <PColumn
              v-else-if="header.field === 'name'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                <template v-if="slotProps.data.removed_at">{{
                  slotProps.data.name
                }}</template>
                <router-link
                  v-else
                  :to="{
                    name: 'project',
                    params: {
                      namespace: slotProps.data.workspace,
                      projectName: slotProps.data.name
                    }
                  }"
                  class="font-semibold"
                >
                  {{ slotProps.data.name }}
                </router-link>
              </template>
            </PColumn>

            <PColumn
              v-else-if="header.field === 'updated'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                <span :title="$filters.datetime(slotProps.data.updated)">
                  {{ $filters.timediff(slotProps.data.updated) }}
                </span>
              </template>
            </PColumn>

            <PColumn
              v-else-if="header.field === 'disk_usage'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                {{ $filters.filesize(slotProps.data.disk_usage, 'MB') }}
              </template>
            </PColumn>

            <PColumn
              v-else-if="header.field === 'removed_at'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                <span
                  :title="`Scheduled for removal at ${$filters.datetime(
                    slotProps.data.removed_at
                  )}`"
                >
                  {{ $filters.timediff(slotProps.data.removed_at) }}
                </span>
              </template>
            </PColumn>

            <PColumn v-else-if="header.field === 'buttons'">
              <template #body="slotProps">
                <div
                  class="justify-center px-0"
                  v-if="slotProps.data.removed_at"
                >
                  <div class="flex align-items-center gap-1">
                    <PButton
                      label="Restore"
                      severity="secondary"
                      size="small"
                      @click="confirmRestore(slotProps.data)"
                    />
                    <PButton
                      label="Delete"
                      severity="danger"
                      size="small"
                      @click="confirmDelete(slotProps.data)"
                    />
                  </div>
                </div>
              </template>
            </PColumn>

            <PColumn
              v-else
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            ></PColumn>
          </template>
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
  useDialogStore,
  useNotificationStore,
  SortingOptions,
  TableDataHeader,
  AppSection,
  AppContainer,
  ConfirmDialogProps
} from '@mergin/lib'
import debounce from 'lodash/debounce'
import { mapActions, mapState } from 'pinia'
import {
  DataTablePageEvent,
  DataTableRowClickEvent,
  DataTableSortEvent
} from 'primevue/datatable'
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
  data() {
    return {
      options: Object.assign({}, this.initialOptions),
      search: '',
      abortController: null as AbortController | null
    }
  },
  computed: {
    ...mapState(useAdminStore, ['projects']),
    headers(): TableDataHeader[] {
      return [
        ...(this.showNamespace
          ? [
              {
                header: 'Workspace',
                field: 'workspace',
                sortable: true
              }
            ]
          : []),
        { header: 'Name', field: 'name', sortable: true },
        { header: 'Last Update', field: 'updated', sortable: true },
        { header: 'Size', field: 'disk_usage', sortable: true },
        { header: 'Scheduled removal at', field: 'removed_at', sortable: true },
        { header: 'Removed by', field: 'removed_by', sortable: true },
        { header: '', field: 'buttons', sortable: false }
      ]
    }
  },
  created() {
    // Restore any search/sort/page state from the URL before the first fetch
    this.initFromQuery()
    // Delay search-triggered fetches so rapid typing doesn't spam the API
    this.onSearch = debounce(this.onSearch, 500)
    this.doFetch()
  },
  methods: {
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    ...mapActions(useNotificationStore, ['error', 'show']),
    ...mapActions(useAdminStore, [
      'getProjects',
      'restoreProject',
      'deleteProject'
    ]),

    // Seed local state from URL query params so the page is shareable / survives navigation
    initFromQuery() {
      const q = this.$route.query
      if (q.q) this.search = String(q.q)
      if (q.page) this.options.page = Number(q.page)
      if (q.per_page) this.options.itemsPerPage = Number(q.per_page)
      if (q.order_by) this.options.sortBy[0] = String(q.order_by)
      if (q.desc) this.options.sortDesc[0] = q.desc === 'true'
    },

    // Reflect current search/sort/page state into the URL (defaults are omitted to keep URLs clean)
    updateQuery() {
      const query: Record<string, string> = {}
      if (this.search) query.q = this.search
      if (this.options.page > 1) query.page = String(this.options.page)
      if (this.options.itemsPerPage !== 20)
        query.per_page = String(this.options.itemsPerPage)
      if (this.options.sortBy[0] && this.options.sortBy[0] !== 'updated')
        query.order_by = this.options.sortBy[0]
      if (!this.options.sortDesc[0]) query.desc = 'false'
      // replace (not push) so back-button skips intermediate search states
      this.$router.replace({ query })
    },

    // Single entry point for all fetches: cancels any in-flight request, syncs the URL, then fetches
    doFetch() {
      // Abort the previous request so a stale slower response can't overwrite a newer one
      this.abortController?.abort()
      this.abortController = new AbortController()
      this.updateQuery()
      this.getProjects({
        params: { ...this.options, like: this.search },
        signal: this.abortController.signal
      })
    },

    paginating(options) {
      this.options = options
      this.doFetch()
    },

    // Called on every keystroke (debounced); resets to page 1 so results start from the beginning
    onSearch() {
      this.options.page = 1
      this.doFetch()
    },

    onPage(event: DataTablePageEvent) {
      this.options.page = event.page + 1
      this.options.itemsPerPage = event.rows
      this.doFetch()
    },

    onSort(event: DataTableSortEvent) {
      this.options.sortBy[0] = event.sortField?.toString()
      this.options.sortDesc[0] = event.sortOrder < 1
      this.doFetch()
    },

    rowClick(event: DataTableRowClickEvent) {
      // Removed projects have no detail view, only Restore/Delete buttons
      if (event.data.removed_at) return

      const originalEvent = event.originalEvent as MouseEvent
      // Let the browser handle clicks that originate from a link or button inside the row
      if ((originalEvent.target as HTMLElement).closest('a, button')) return

      const location = {
        name: AdminRoutes.PROJECT,
        params: {
          namespace: event.data.workspace,
          projectName: event.data.name
        }
      }
      // Ctrl/Cmd/Shift+click opens in a new tab; plain click navigates in the same tab
      if (originalEvent.ctrlKey || originalEvent.metaKey || originalEvent.shiftKey) {
        window.open(this.$router.resolve(location).href, '_blank')
      } else {
        this.$router.push(location)
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
    },

    onRefresh() {
      this.doFetch()
    }
  }
})
</script>

<style lang="scss" scoped></style>
