# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
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
    <v-data-iterator
    :options="options"
    :items="projects"
    :server-items-length="numberOfItems"
    v-on:update:options="paginating"
    item-key="updated"
    :loading="loading"
    :hide-default-footer="true"
    style="background-color: #ffffff"
    flat
    no-data-text="No projects found"
    >
      <template v-slot:header>
        <v-toolbar
          color=""
          class="mb-1"
          flat
          v-if="showHeader"
        >
          <v-text-field
            v-model="searchFilterByProjectName"
            clearable
            flat
            hide-details
            prepend-inner-icon="mdi-magnify"
            label="Search projects"
            @input="filterData"
            style="margin-right:8px;"
          >
          </v-text-field>
          <template v-if="$vuetify.breakpoint.smAndUp">
            <v-select
              v-model="options.sortBy[0]"
              @change="paginating(options)"
              flat
              hide-details
              :items="selectKeys"
              prepend-inner-icon="sort_by_alpha"
            ></v-select>
            <v-spacer></v-spacer>
            <v-btn-toggle
              v-model="options.sortDesc[0]"
              @change="paginating(options)"
              mandatory
            >
              <v-btn
                large
                depressed
                color="#ffffff"
                :value="false"
              >
                <v-icon>mdi-arrow-up</v-icon>
              </v-btn>
              <v-btn
                large
                depressed
                color="#ffffff"
                :value="true"
              >
                <v-icon>mdi-arrow-down</v-icon>
              </v-btn>
            </v-btn-toggle>
          </template>
        </v-toolbar>
      </template>
      <template v-slot:item="{ item }">
    <v-card :outlined="false"
            class="mx-auto"
            flat>
      <v-list-item three-line>
      <v-list-item-content>
        <v-list-item-title class="headline mb-1">
          <router-link :to="{ name: 'project', params: { namespace: item.namespace, projectName: item.name }}"><b><span v-if="showNamespace">{{item.namespace}} /</span> {{item.name}}</b></router-link>
              <v-chip
              elevation="0"
              v-if="item.access.public"
              style="margin-left: 8px;"
              outlined
              color="primary"
            >
              Public
            </v-chip>
        </v-list-item-title>
        <v-list-item-subtitle>{{item.description}}</v-list-item-subtitle>
        <div style="font-size: smaller">
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-on="on" style="margin-right: 20px;"><v-icon class="icon" size="20">share</v-icon>{{ item.access.readers.length }}</span>
            </template>
            <span>collaborators</span>
          </v-tooltip>
          <v-tooltip bottom
                      v-if="item.version">
            <template v-slot:activator="{ on }">
            <span v-on="on" style=" margin-right: 20px;">
              <router-link :to="{ name: 'project-versions', params: { namespace: item.namespace, projectName: item.name }}">
                <span style="font-size: smaller"><v-icon class="icon" size="20">history</v-icon>{{ item.version.substr(1) }}</span>
              </router-link>
            </span>
            </template>
            <span>versions</span>
          </v-tooltip>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-on="on" style="margin-right: 20px;"><v-icon class="icon" size="20">folder</v-icon>{{ item.disk_usage | filesize('MB', 1) }}</span>
            </template>
            <span>project size</span>
          </v-tooltip>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-on="on" style=" margin-right: 20px;">Updated {{ item.updated | timediff }}</span>
            </template>
            <span >{{ item.updated | datetime }}</span>
          </v-tooltip>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-if="!item.tags.includes('valid_qgis')" v-on="on" style=" margin-right: 20px;"><v-icon color="#fb8c0087" size="20">warning</v-icon></span>
            </template>
            <span>Missing QGIS project file</span>
          </v-tooltip>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-if="item.has_conflict" v-on="on" style=" margin-right: 20px;"><v-icon color="#fb8c0087" size="20">error</v-icon></span>
            </template>
            <span>There is conflict file in project</span>
          </v-tooltip>
        </div>
      </v-list-item-content>
      </v-list-item>
      <v-divider
      style="color:black"/>

    </v-card>
      </template>
      <template  v-slot:footer="{ pagination, options }">
        <div class="text-center">
          <v-pagination
            v-if="showFooter && numberOfItems > options.itemsPerPage"
            v-model="options.page"
            :length="Math.ceil(numberOfItems / options.itemsPerPage)"
            :total-visible="7"
            circle
            color="primary"
            @input="fetchPage"
          ></v-pagination>
        </div>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
import { waitCursor, removeAccents, formatToTitle } from '../util'
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
    showHeader: {
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
        itemsPerPage: 25,
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
      projects: [],
      keys: ['name', 'owner', 'updated', 'disk_usage'],
      sortBy: ''
    }
  },
  computed: {
    ...mapState(['app']),
    header () {
      let header = []
      if (this.showNamespace) {
        header.push({ text: 'Owner', value: 'namespace', sortable: this.sortable })
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
    selectKeys () {
      return this.keys.map(i => {
        return { text: formatToTitle(i), value: i }
      })
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
    fetchPage (number) {
      this.options.page = number
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
        params.name = this.searchFilterByProjectName.trim()
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
.v-data-iterator {
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
    font-size: 1rem;
  }
  .v-chip {
    margin: 0;
    margin-right: 0.5em;
    height: 1.3em;
    ::v-deep .v-chip__content {
      padding: 0 0.2em;
      font-size: 85%;
    }
  }
  .hidden {
    opacity: 0;
    pointer-events: none;
  }
}
.icon {
  margin-right: 5px;
}
.v-input {
  padding-top: 0!important;
  margin-top: 0!important;
}

.v-toolbar {
  ::v-deep .v-toolbar__content {
     padding-left: 0px;
  }
}

.v-list-item {
  padding-left: 0px;
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
