<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
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
        <v-toolbar color="" class="mb-1" flat v-if="showHeader">
          <v-text-field
            v-model="searchFilterByProjectName"
            clearable
            flat
            hide-details
            prepend-inner-icon="mdi-magnify"
            label="Search projects"
            @input="filterData"
            style="margin-right: 8px"
            data-cy="project-table-search-bar"
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
              data-cy="project-table-sort-type"
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
                data-cy="project-table-sort-btn-up"
              >
                <v-icon>mdi-arrow-up</v-icon>
              </v-btn>
              <v-btn
                large
                depressed
                color="#ffffff"
                :value="true"
                data-cy="project-table-sort-btn-down"
              >
                <v-icon>mdi-arrow-down</v-icon>
              </v-btn>
            </v-btn-toggle>
          </template>
        </v-toolbar>
      </template>
      <template v-slot:item="{ item }">
        <v-card
          :outlined="false"
          class="mx-auto"
          data-cy="project-table-card"
          flat
        >
          <v-list-item three-line>
            <v-list-item-content>
              <v-list-item-title class="text-h5 mb-1">
                <router-link
                  :to="{
                    name: 'project',
                    params: {
                      namespace: item.namespace,
                      projectName: item.name
                    }
                  }"
                  ><b>
                    <span v-if="showNamespace">{{ item.namespace }} /</span>
                    {{ item.name }}</b
                  ></router-link
                >
                <v-chip
                  elevation="0"
                  v-if="item.access.public && !onlyPublic"
                  style="margin-left: 8px"
                  outlined
                  color="primary"
                >
                  Public
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle
                >{{ item.description }}
              </v-list-item-subtitle>
              <div style="font-size: smaller">
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <span
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-collaborators"
                      ><v-icon class="icon" size="20">share</v-icon
                      >{{ item.access.readers.length }}</span
                    >
                  </template>
                  <span>collaborators</span>
                </v-tooltip>
                <v-tooltip bottom v-if="item.version">
                  <template v-slot:activator="{ on }">
                    <span
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-history"
                    >
                      <router-link
                        :to="{
                          name: 'project-versions',
                          params: {
                            namespace: item.namespace,
                            projectName: item.name
                          }
                        }"
                      >
                        <span style="font-size: smaller"
                          ><v-icon class="icon" size="20">history</v-icon
                          >{{ item.version.substr(1) }}</span
                        >
                      </router-link>
                    </span>
                  </template>
                  <span>versions</span>
                </v-tooltip>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <span
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-project-size"
                      ><v-icon class="icon" size="20">folder</v-icon
                      >{{ item.disk_usage | filesize('MB', 1) }}</span
                    >
                  </template>
                  <span>project size</span>
                </v-tooltip>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <span
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-updated"
                      >Updated {{ item.updated | timediff }}</span
                    >
                  </template>
                  <span>{{ item.updated | datetime }}</span>
                </v-tooltip>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <span
                      v-if="!item.tags.includes('valid_qgis')"
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-missing-project"
                      ><v-icon color="#fb8c0087" size="20"
                        >warning</v-icon
                      ></span
                    >
                  </template>
                  <span>Missing QGIS project file</span>
                </v-tooltip>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <span
                      v-if="item.has_conflict"
                      v-on="on"
                      style="margin-right: 20px"
                      data-cy="project-form-conflict-file"
                      ><v-icon color="#fb8c0087" size="20">error</v-icon></span
                    >
                  </template>
                  <span>There is conflict file in project</span>
                </v-tooltip>
              </div>
            </v-list-item-content>
          </v-list-item>
          <v-divider style="color: black" />
        </v-card>
      </template>
      <template v-slot:footer="{ options }">
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

<script lang="ts">
import debounce from 'lodash/debounce'
import { defineComponent, PropType } from 'vue'

import { PaginatedGridOptions } from '@/common'
import { formatToTitle } from '@/common/text_utils'
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
    sortable: {
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
      type: Object as PropType<PaginatedGridOptions>,
      default: () => ({
        sortBy: ['updated'],
        sortDesc: [true],
        itemsPerPage: 25,
        page: 1
      })
    },
    numberOfItems: {
      type: Number,
      default: 0
    },
    projects: Array as PropType<Array<ProjectListItem>>
  },
  data() {
    return {
      options: Object.assign({}, this.initialOptions),
      searchFilterByProjectName: '',
      searchFilterByNamespace: '',
      searchFilterByDay: '',
      loading: false,
      keys: ['name', 'updated', 'disk_usage'],
      sortBy: ''
    }
  },
  computed: {
    header() {
      let header = []
      if (this.showNamespace) {
        header.push({
          text: 'Owner',
          value: 'namespace',
          sortable: this.sortable
        })
      }
      header = header.concat(
        { text: 'Name', value: 'name', sortable: this.sortable },
        { text: '', width: 90, sortable: false },
        { text: 'Last Update', value: 'updated', sortable: this.sortable },
        { text: 'Size', value: 'meta.size', sortable: this.sortable }
      )
      return header
    },
    selectKeys() {
      return this.keys.map((i) => {
        return { text: formatToTitle(i), value: i }
      })
    }
  },
  watch: {
    $route: {
      immediate: false,
      handler: 'changedRoute'
    }
  },
  created() {
    this.filterData = debounce(this.filterData, 3000)
  },
  methods: {
    paginating(options) {
      this.options = options
      this.fetchProjects()
    },
    fetchPage(number) {
      this.options.page = number
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
    changeSort(column) {
      if (this.pagination.sortBy === column) {
        this.pagination.descending = !this.pagination.descending
      } else {
        this.pagination.sortBy = column
        this.pagination.descending = false
      }
    },
    filterData() {
      this.options.page = 1
      this.fetchProjects()
    }
  }
})
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

    :deep(.v-chip__content) {
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
  padding-top: 0 !important;
  margin-top: 0 !important;
}

.v-toolbar {
  :deep(.v-toolbar__content) {
    padding-left: 0;
  }
}

.v-list-item {
  padding-left: 0;
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
