# Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <v-data-table
      :headers="header"
      :items="projects"
      ref="table"
      no-data-text="No removed projects"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="count <= 10"
      item-key="updated"
      :options="options"
      :server-items-length="count"
      v-on:update:options="paginating"
      :loading="loading"
      loading-text="Loading... Please wait"
    >
      <template v-slot:item="{ item }">
        <tr>
          <td>
            {{ item.namespace }}
          </td>
          <td>
            {{ item.name }}
          </td>
          <td>
            {{ item.properties.disk_usage | filesize('MB')}}
          </td>
          <td>
            {{ item.properties.latest_version }}
          </td>
          <td>
            <v-tooltip bottom>
              <template v-slot:activator="{ on }">
              <span v-on="on">{{ item.timestamp | timediff }}</span>
              </template>
              <span>{{ item.timestamp | datetime }}</span>
            </v-tooltip>
          </td>
          <td>
              {{ item.removed_by }}
          </td>
          <td class="justify-center px-0">
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
          </td>
        </tr>
      </template>
    </v-data-table>
</template>

<script>
import { waitCursor } from '@/util'
import debounce from 'debounce'
import CommonAPI from '@/admin/mixins/CommonAPI'


export default {
  name: 'removed-projects-table',
  mixins: [CommonAPI],
  data () {
    return {
      options: {
        sortBy: ['timestamp'],
        sortDesc: [true],
        itemsPerPage: 25,
        page: 1
      },
      loading: false,
      header: [
        { text: 'Owner', value: 'namespace', sortable: true },
        { text: 'Name', value: 'name', sortable: true },
        { text: 'Size', value: 'properties.disk_usage', sortable: false },
        { text: 'Version', value: 'properties.latest_version', sortable: false },
        { text: 'Removed', value: 'timestamp', sortable: true },
        { text: 'Removed by', value: 'removed_by', sortable: false },
        { text: '', sortable: false }
      ],
      projects: [],
      count: 0
    }
  },
  created () {
    this.filterData = debounce(this.filterData, 3000)
  },
  methods: {
    paginating (options) {
      this.options = options
      this.fetchProjects()
    },
    async fetchProjects () {
      this.loading = true
      const params = {
        page: this.options.page,
        per_page: this.options.itemsPerPage
      }
      if (this.options.sortBy[0]) {
        params.descending = this.options.sortDesc[0]
        params.order_by = this.options.sortBy[0]
      }
      const result = await this.fetchRemovedProjects(params)
      if (result.success) {
        this.projects = result.projects
        this.count = result.count
      } else {
        this.$notification.error(result.message)
      }
      this.loading = false
    },
    async deleteProject (id) {
      waitCursor(true)
      const result = await this.removeProject(id)
      if (result.success) {
        const index = this.projects.findIndex(i => i.id === id)
        this.projects.splice(index, 1)
        this.$notification.show('Project removed successfully')
      } else {
        this.$notification.error(result.message)
      }
      waitCursor(false)
    },
    restoreProjectConfirmation (item) {
      const props = {
        text: `Are you sure to restore project <strong>${item.namespace}/${item.name}?</strong>`,
        confirmText: 'Restore'
      }
      const listeners = {
        confirm: async () => {
          waitCursor(true)
          const result = await this.restoreProject(item.id)
          if (result.success) {
            const index = this.projects.findIndex(i => i.id === item.id)
            this.projects.splice(index, 1)
            this.$notification.show('Project restored successfully')
          } else {
            this.$notification.error(result.message)
          }
          waitCursor(false)
        }
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    removeProjectConfirmation (item) {
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
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    changeSort (column) {
      if (this.pagination.sortBy === column) {
        this.pagination.descending = !this.pagination.descending
      } else {
        this.pagination.sortBy = column
        this.pagination.descending = false
      }
    },
    filterData () {
      this.options.page = 1
      this.fetchProjects()
    }
  }
}
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
    margin-right: 0.3em;
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
  padding-top: 0!important;
  margin-top: 0!important;
}

.v-list__tile__title{
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
