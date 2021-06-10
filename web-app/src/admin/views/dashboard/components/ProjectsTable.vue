# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <portal to="additional-action" class="xxx">
        <v-menu
          class="filter-menu"
          :close-on-content-click="false">
          <template v-slot:activator="{ on: menu, attrs }">
             <v-tooltip
              top>
          <template v-slot:activator="{ on: tooltip }">
          <v-btn
            :class="(searchFilterByNamespace || searchFilterByProjectName || searchFilterByDay) ? 'activate': ''"
            v-bind="attrs"
            v-on="{ ...tooltip, ...menu }"
            icon small
          >
            Filter <v-icon>filter_list</v-icon>
          </v-btn>
          </template>
        <span>Filter data</span>
      </v-tooltip>
    </template>
          <v-list dense>
            <v-list-item > <!-- v-if="showNamespace" -->
              <v-list-item-title>Namespace</v-list-item-title>
              <v-list-item-action>
                <v-text-field
                  class="search"
                  placeholder="Filter by owner"
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
            <v-list-item>
              <v-list-item-title>Last update in</v-list-item-title>
              <v-list-item-action>
                <v-text-field
                  type="number"
                  min="0"
                  class="search"
                  placeholder="Filter by XX days old"
                  append-icon="search"
                  v-model="searchFilterByDay"
                  @input="filterData"
                  hide-details
                />
              </v-list-item-action>
            </v-list-item>
          </v-list>
        </v-menu>
    </portal>
    <portal to="delete-button">
      <v-btn
        :disabled="!selected.length"
        @click="confirmDelete"
        class="error--text"
        rounded
      >
        <v-icon class="mr-2">remove_circle</v-icon>
        Delete
      </v-btn>
    </portal>
    <portal to="accept-request-button">
      <v-btn
        :disabled="!selected.length"
        @click="confirmAcceptRequest"
        class="success--text"
        rounded
      >
        Accept request
      </v-btn>
    </portal>
    <v-data-table
      :headers="header"
      :items="projects"
      ref="table"
      no-data-text="No projects"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="numberOfItems <= 10 || !showFooter"
      v-model="selected"
      item-key="updated"
      :options="options"
      :server-items-length="numberOfItems"
      v-on:update:options="paginating"
      :loading="loading"
      loading-text="Loading... Please wait"
    >
      <template v-slot:item="{ item }">
        <tr>
        <td v-if="showNamespace">
          <router-link :to="{name: `${asAdmin ? 'admin-': ''}namespace-projects`, params: {namespace: item.namespace}}">
            <strong>{{ item.namespace }}</strong>
          </router-link>
        </td>
        <td>
          <router-link :to="{name: `${asAdmin ? 'admin-': ''}project`, params: {namespace: item.namespace, projectName: item.name}}">
            <strong>{{ item.name }}</strong>
          </router-link>
        </td>
        <td class="flags">
          <v-tooltip bottom
            v-if="!item.access.public">
            <template v-slot:activator="{ on }">
            <v-icon
              v-text="'lock'"
              small
              v-on="on"
            />
            </template>
            <span>Private project</span>
          </v-tooltip>
          <v-tooltip bottom :class="{ hidden: !item.permissions.upload }">
            <template v-slot:activator="{ on }">
            <v-icon
              v-text="'cloud_upload'"
              small
              v-on="on"
            />
            </template>
            <span>Can upload</span>
          </v-tooltip>
        </td>
        <td>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-on="on">{{ item.updated | timediff }}</span>
            </template>
            <span>{{ item.updated | datetime }}</span>
          </v-tooltip>
        </td>
        <td>
            {{ item.disk_usage | filesize('MB') }}
        </td>
        <td v-if="isRequest()">
          <strong>{{ item.transfers[0].to_ns_name }}</strong>
        </td>
        </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import { waitCursor, removeAccents } from '@/util'
import { mapState } from 'vuex'

import pickBy from 'lodash/pickBy'
import mapValues from 'lodash/mapValues'
import debounce from 'debounce'


const TagsLabels = {
  valid_qgis: 'QGIS',
  input_use: 'Input',
  mappin_use: 'Mappin'
}

export default {
  name: 'projects-table',
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
  data () {
    return {
      options: Object.assign({}, this.initialOptions),
      activeTags: [],
      selected: [],
      searchFilterByProjectName: '',
      searchFilterByNamespace: '',
      searchFilterByDay: '',
      numberOfItems: 0,
      loading: false,
      projects: []
    }
  },
  computed: {
    ...mapState(['app']),
    header () {
      let header = []
      if (this.showNamespace) {
        header.push({ text: 'Namespace', value: 'namespace', sortable: this.sortable })
      }
      header = header.concat(
        { text: 'Name', value: 'name', sortable: this.sortable },
        { text: '', width: 90, sortable: false },
        { text: 'Last Update', value: 'updated', sortable: this.sortable },
        { text: 'Size', value: 'meta.size', sortable: this.sortable }
      )
      if (this.isRequest()) {
        header.push({ text: 'Transferred to', value: 'transfers[0].to_ns_name', sortable: false })
      }
      return header
    },
    tags () {
      return mapValues(TagsLabels, (v, k) => ({
        label: TagsLabels[k],
        active: this.activeTags.includes(k)
      }))
    }
  },
  watch: {
    $route: {
      immediate: true,
      handler: 'changedRoute'
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
    changedRoute () {
      this.options.page = 1
      this.fetchProjects()
    },
    fetchProjects () {
      this.loading = true
      this.tagsFromQuery()
      let params = {}
      params = (this.$route.name === 'shared_projects' || this.$route.name === 'my_projects') ? { flag: this.$route.meta.flag } : {}
      params.page = this.options.page
      params.per_page = this.options.itemsPerPage
      if (this.options.sortBy[0]) {
        let orderParam = ''
        if (this.options.sortBy[0] === 'meta.size') {
          orderParam = 'disk_usage'
        } else {
          orderParam = this.options.sortBy[0] === 'owner' ? 'namespace' : this.options.sortBy[0]
        }
        params.order_params = orderParam + (this.options.sortDesc[0] ? '_desc' : '_asc')
      }
      if (this.searchFilterByProjectName) {
        params.name = removeAccents(this.searchFilterByProjectName.trim())
      }
      if (this.searchFilterByNamespace) {
        params.namespace = removeAccents(this.searchFilterByNamespace.trim())
      }
      if (this.activeTags.length) {
        params.tags = this.activeTags
      }
      if (this.namespace) {
        params.only_namespace = this.namespace
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
      if (this.searchFilterByDay && this.searchFilterByDay >= 0) {
        params.last_updated_in = this.searchFilterByDay
      }
      this.$http('/v1/project/paginated', { params })
        .then(resp => {
          this.projects = resp.data.projects
          this.numberOfItems = resp.data.count
          this.loading = false
        })
        .catch(() => {
          this.$notification.error('Failed to fetch list of projects')
        })
    },
    isRequest () {
      return this.$route.meta.flag === 'request'
    },
    tagsFromQuery () {
      const tags = this.$route.query.tags
      this.activeTags = tags ? tags.split(',') : []
    },
    toggleTag (tag) {
      if (this.activeTags.includes(tag)) {
        this.activeTags = this.activeTags.filter(t => t !== tag)
      } else {
        this.activeTags.push(tag)
      }

      let { path, query } = this.$route
      query = {
        ...query,
        tags: Object.keys(pickBy(this.tags, t => t.active)).join(',')
      }
      // clean from empty parameters
      query = pickBy(query, param => param && param.length)
      this.$router.push({ path, query })
    },
    addTag (tag) {
      if (!this.tags[tag].active) {
        this.toggleTag(tag)
      }
    },
    selectedShowedProjects () {
      const selected = []
      const that = this
      this.$refs.table.filteredItems.forEach(function (project) {
        const identifier = that.projectIdentifier(project)
        if (that.selected.includes(identifier)) {
          selected.push(identifier)
        }
      })
      return selected
    },
    deleteProjects (selectedProjects) {
      waitCursor(true)
      const promises = selectedProjects.map(id => {
        const params = {
          'axios-retry': { retries: 5 }
        }
        return this.$http.delete(`/v1/project/${id}`, params)
      })

      Promise.all(promises).then(() => {
        this.selected = []
        this.fetchProjects()
        waitCursor(false)
      }).catch(err => {
        const msg = (err.response && err.response.status === 503) ? err.response.data.detail : 'Unable to remove projects'
        this.$notification.error(msg)
        waitCursor(false)
      })
    },
    confirmDelete () {
      const selected = this.selectedShowedProjects()
      if (selected.length === 0) {
        return
      }
      const props = {
        text: 'Are you sure to delete project ' + selected.join(', ') + '?',
        confirmText: 'Delete'
      }
      const listeners = {
        confirm: () => this.deleteProjects(selected)
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    acceptProjectRequests (selectedProjects) {
      waitCursor(true)
      const promises = selectedProjects.map(id => {
        const params = {
          'axios-retry': { retries: 5 }
        }
        return this.$http.post(`/v1/project/transfer/${id}`, params)
      })

      Promise.all(promises).then(() => {
        this.selected = []
        this.fetchProjects()
        waitCursor(false)
      }).catch(err => {
        const msg = (err.response && err.response.status === 503) ? err.response.data.detail : 'Unable to remove projects'
        this.$notification.error(msg)
        waitCursor(false)
      })
    },
    confirmAcceptRequest () {
      let selected = this.selectedShowedProjects()
      if (selected.length === 0) {
        return
      }
      const props = {
        text: 'Are you sure to accept the projects ' + selected.join(', ') + '?',
        confirmText: 'Accept'
      }

      // get the transfer id
      selected = []
      const that = this
      this.$refs.table.filteredItems.forEach(function (project) {
        const identifier = that.projectIdentifier(project)
        if (that.selected.includes(identifier)) {
          selected.push(project.transfer)
        }
      })
      const listeners = {
        confirm: () => {
          this.acceptProjectRequests(selected)
        }
      }
      this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
    },
    projectIdentifier (project) {
      return project.namespace + '/' + project.name
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
