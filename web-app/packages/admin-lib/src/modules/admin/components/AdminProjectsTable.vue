<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <portal to="additional-action" class="xxx">
      <v-menu class="filter-menu" :close-on-content-click="false">
        <template v-slot:activator="{ on: menu, attrs }">
          <v-tooltip top>
            <template v-slot:activator="{ on: tooltip }">
              <v-btn
                :class="searchFilterByNamespace || searchFilterByProjectName"
                v-bind="attrs"
                v-on="{ ...tooltip, ...menu }"
                icon
                small
              >
                Filter
                <v-icon>filter_list</v-icon>
              </v-btn>
            </template>
            <span>Filter data</span>
          </v-tooltip>
        </template>
        <v-list dense>
          <v-list-item v-if="showNamespace">
            <v-list-item-title>Workspace</v-list-item-title>
            <v-list-item-action>
              <v-text-field
                class="search"
                placeholder="Filter by workspace"
                append-icon="search"
                v-model="searchFilterByNamespace"
                @input="filterData"
                hide-details
              />
            </v-list-item-action>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Project name</v-list-item-title>
            <v-list-item-action>
              <v-text-field
                class="search"
                placeholder="Filter by project name"
                append-icon="search"
                v-model="searchFilterByProjectName"
                @input="filterData"
                hide-details
              />
            </v-list-item-action>
          </v-list-item>
        </v-list>
      </v-menu>
    </portal>
    <v-data-table
      :headers="header"
      :items="projects"
      ref="table"
      no-data-text="No projects"
      color="primary"
      :footer-props="{ 'items-per-page-options': [10, 25, 50] }"
      :hide-default-footer="numberOfItems <= 10 || !showFooter"
      item-key="updated"
      :options="options"
      :server-items-length="numberOfItems"
      v-on:update:options="paginating"
      :loading="loading"
      loading-text="Loading... Please wait"
    >
      <template v-if="showNamespace" #item.namespace="{ value }">
        <router-link
          :to="{
            name: `namespace-projects`,
            params: { namespace: value }
          }"
        >
          <strong>{{ value }}</strong>
        </router-link>
      </template>
      <template #item.name="{ value, item }">
        <router-link
          :to="{
            name: 'project',
            params: { namespace: item.namespace, projectName: value }
          }"
        >
          <strong>{{ value }}</strong>
        </router-link>
      </template>

      <template #item.updated="{ value }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <span v-on="on">{{ value | timediff }}</span>
          </template>
          <span>{{ value | datetime }}</span>
        </v-tooltip>
      </template>

      <template #item.meta.size="{ item }">
        {{ item.disk_usage | filesize('MB') }}
      </template>

      <template #item.removed_at="{ value }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <span v-on="on">{{ value | timediff }}</span>
          </template>
          <span>{{ value | datetime }}</span>
        </v-tooltip>
      </template>

      <template #item.removed_by="{ value }">
        <span>{{ value }}</span>
      </template>

      <template #item.buttons="{ item }">
        <div class="justify-center px-0" v-if="item.removed_at">
          <div style="text-align: end">
            <v-chip
              @click="restoreProjectConfirmation(item)"
              elevation="0"
              color="green"
              class="white--text"
            >
              restore
            </v-chip>
            <v-chip
              @click="removeProjectConfirmation(item)"
              elevation="0"
              color="red"
              class="white--text"
            >
              remove
            </v-chip>
          </div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import {
  ApiRequestSuccessInfo,
  ConfirmDialog,
  errorUtils,
  htmlUtils,
  useDialogStore,
  useNotificationStore
} from '@mergin/lib'
import { mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { AdminApi, PaginatedAdminProjectsParams } from '@/main'

export default defineComponent({
  name: 'projects-table',
  props: {
    showNamespace: Boolean,
    sortable: {
      type: Boolean,
      default: true
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    initialOptions: {
      type: Object,
      default: () => ({
        sortBy: ['updated'],
        sortDesc: [true],
        itemsPerPage: 10,
        page: 1
      })
    }
  },
  data() {
    return {
      options: Object.assign({}, this.initialOptions),
      searchFilterByProjectName: '',
      searchFilterByNamespace: '',
      numberOfItems: 0,
      loading: false,
      projects: []
    }
  },
  computed: {
    header() {
      return [
        ...(this.showNamespace
          ? [
              {
                text: 'Workspace',
                value: 'namespace',
                sortable: this.sortable
              }
            ]
          : []),
        { text: 'Name', value: 'name', sortable: this.sortable },
        { text: 'Last Update', value: 'updated', sortable: this.sortable },
        { text: 'Size', value: 'meta.size', sortable: this.sortable },
        { text: 'Removed', value: 'removed_at', sortable: true },
        { text: 'Removed by', value: 'removed_by', sortable: true },
        { text: '', value: 'buttons', sortable: false }
      ]
    }
  },
  watch: {
    $route: {
      immediate: false,
      handler: 'changedRoute'
    }
  },
  created() {
    // this.filterData = debounce(this.filterData, 3000)
  },
  methods: {
    ...mapActions(useDialogStore, { showDialog: 'show' }),
    ...mapActions(useNotificationStore, ['error', 'show']),

    paginating(options) {
      this.options = options
      this.fetchProjects()
    },

    changedRoute() {
      this.options.page = 1
      this.fetchProjects()
    },

    fetchProjects() {
      this.loading = true
      const params: PaginatedAdminProjectsParams = {
        page: this.options.page,
        per_page: this.options.itemsPerPage
      }
      if (this.options.sortBy[0]) {
        let orderParam = ''
        if (this.options.sortBy[0] === 'meta.size') {
          orderParam = 'disk_usage'
        } else {
          orderParam =
            this.options.sortBy[0] === 'namespace'
              ? 'workspace'
              : this.options.sortBy[0]
        }
        params.order_params =
          orderParam + (this.options.sortDesc[0] ? ' DESC' : ' ASC')
      }
      if (this.searchFilterByProjectName) {
        params.name = this.searchFilterByProjectName.trim()
      }
      if (this.searchFilterByNamespace) {
        params.workspace = this.searchFilterByNamespace.trim()
      }
      AdminApi.getPaginatedAdminProject(params)
        .then((resp) => {
          this.projects = resp.data.projects
          this.numberOfItems = resp.data.count
          this.loading = false
        })
        .catch((e) => {
          console.warn('Failed to fetch list of projects', e)
          this.error({
            text: 'Failed to fetch list of projects'
          })
        })
    },

    filterData() {
      this.options.page = 1
      this.fetchProjects()
    },

    async deleteProject(id) {
      htmlUtils.waitCursor(true)

      const result = {} as ApiRequestSuccessInfo
      try {
        await AdminApi.removeProject(id)
        result.success = true
      } catch (e) {
        result.success = false
        result.message = errorUtils.getErrorMessage(
          e,
          'Unable to remove project'
        )
      }

      if (result.success) {
        const index = this.projects.findIndex((i) => i.id === id)
        this.projects.splice(index, 1)
        await this.show({
          text: 'Project removed successfully'
        })
      } else {
        await this.error({
          text: result.message
        })
      }
      htmlUtils.waitCursor(false)
    },

    restoreProjectConfirmation(item) {
      const props = {
        text: `Are you sure to restore project <strong>${item.namespace}/${item.name}?</strong>`,
        confirmText: 'Restore'
      }
      const listeners = {
        confirm: async () => {
          htmlUtils.waitCursor(true)

          const result = {} as ApiRequestSuccessInfo
          try {
            await AdminApi.restoreProject(item.id)
            result.success = true
          } catch (e) {
            result.success = false
            result.message = errorUtils.getErrorMessage(
              e,
              'Unable to restore project'
            )
          }

          if (result.success) {
            const index = this.projects.findIndex((i) => i.id === item.id)
            this.projects.splice(index, 1)
            await this.show({
              text: 'Project restored successfully'
            })
          } else {
            await this.show({
              text: result.message
            })
          }
          htmlUtils.waitCursor(false)
        }
      }
      this.showDialog({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { maxWidth: 500 } }
      })
    },

    removeProjectConfirmation(item) {
      const props = {
        text: `Are you sure to remove project <strong>${item.namespace}/${item.name}</strong>?
        <br> All files will be <strong>permanently deleted</strong> and project won't be able to be restored anymore.`,
        confirmText: 'Delete'
      }
      const listeners = {
        confirm: () => {
          this.deleteProject(item.id)
        }
      }
      this.showDialog({
        component: ConfirmDialog,
        params: { props, listeners, dialog: { maxWidth: 500 } }
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.v-data-table {
  td {
    text-align: left;

    &.flags {
      .v-icon {
        margin: 0 1px;
        cursor: default;
      }
    }
  }

  a {
    text-decoration: none;
  }

  .v-chip {
    margin: 0;
    margin-right: 0.5em;
    height: 1.6em;

    ::v-deep .v-chip__content {
      cursor: pointer;
      padding: 0 0.5em;
      font-size: 85%;
    }
  }

  .hidden {
    opacity: 0;
    pointer-events: none;
  }
}

.v-input {
  padding-top: 0 !important;
  margin-top: 0 !important;
}

.v-list__tile__title {
  width: 110px;
  font-weight: 800;
}

.filter-menu {
  .activate {
    border: 1px solid black;
    border-radius: 5px;
  }
}
</style>
