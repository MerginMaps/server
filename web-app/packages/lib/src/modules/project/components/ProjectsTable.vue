<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-data-iterator
      :page="options.page"
      :items-per-page="options.itemsPerPage"
      :sort-by="[{ key: options.sortBy, order: options.sortDesc }]"
      :items="projects"
      v-on:update:options="onUpdateOptions"
      item-key="name"
      :loading="loading"
      variant="flat"
    >
      <template v-slot:header>
        <v-toolbar color="" class="mb-1" flat v-if="showHeader">
          <v-text-field
            v-model="searchFilterByProjectName"
            clearable
            variant="underlined"
            hide-details
            prepend-inner-icon="mdi-magnify"
            label="Search projects"
            @update:model-value="filterData"
            style="margin-right: 8px"
            data-cy="project-table-search-bar"
          >
          </v-text-field>
          <template v-if="$vuetify.display.smAndUp">
            <v-select
              v-model="options.sortBy"
              @update:model-value="paginating(options)"
              variant="underlined"
              hide-details
              :items="selectKeys"
              prepend-inner-icon="sort_by_alpha"
              data-cy="project-table-sort-type"
            ></v-select>
            <v-spacer></v-spacer>
            <v-btn-toggle
              v-model="options.sortDesc"
              @update:model-value="paginating(options)"
              mandatory="force"
            >
              <v-btn
                size="large"
                variant="flat"
                color="#ffffff"
                data-cy="project-table-sort-btn-up"
                :value="false"
              >
                <v-icon>mdi-arrow-up</v-icon>
              </v-btn>
              <v-btn
                size="large"
                variant="flat"
                color="#ffffff"
                data-cy="project-table-sort-btn-down"
                :value="true"
              >
                <v-icon>mdi-arrow-down</v-icon>
              </v-btn>
            </v-btn-toggle>
          </template>
        </v-toolbar>
      </template>
      <template v-slot:default="{ items }">
        <v-card
          class="mx-auto"
          data-cy="project-table-card"
          v-for="item in items"
          :key="item.raw.name"
          variant="flat"
        >
          <v-list-item lines="three">
            <v-list-item-title class="text-h5 mb-1">
              <router-link
                :to="{
                  name: 'project',
                  params: {
                    namespace: item.raw.namespace,
                    projectName: item.raw.name
                  }
                }"
                ><b>
                  <span v-if="showNamespace">{{ item.raw.namespace }} /</span>
                  {{ item.raw.name }}</b
                ></router-link
              >
              <v-chip
                elevation="0"
                v-if="item.raw.access.public && !onlyPublic"
                style="margin-left: 8px"
                variant="outlined"
                color="primary"
              >
                Public
              </v-chip>
            </v-list-item-title>

            <v-list-item-subtitle
              >{{ item.raw.description }}
            </v-list-item-subtitle>
            <div style="font-size: smaller">
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <span
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-collaborators"
                    ><v-icon class="icon" size="20">share</v-icon
                    >{{ item.raw.access.readers.length }}</span
                  >
                </template>
                <span>collaborators</span>
              </v-tooltip>
              <v-tooltip location="bottom" v-if="item.raw.version">
                <template v-slot:activator="{ props }">
                  <span
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-history"
                  >
                    <router-link
                      :to="{
                        name: 'project-versions',
                        params: {
                          namespace: item.raw.namespace,
                          projectName: item.raw.name
                        }
                      }"
                    >
                      <span style="font-size: smaller"
                        ><v-icon class="icon" size="20">history</v-icon
                        >{{ item.raw.version.substr(1) }}</span
                      >
                    </router-link>
                  </span>
                </template>
                <span>versions</span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <span
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-project-size"
                    ><v-icon class="icon" size="20">folder</v-icon
                    >{{ $filters.filesize(item.raw.disk_usage, 'MB', 1) }}</span
                  >
                </template>
                <span>project size</span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <span
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-updated"
                    >Updated {{ $filters.timediff(item.raw.updated) }}</span
                  >
                </template>
                <span>{{ $filters.datetime(item.raw.updated) }}</span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <span
                    v-if="!item.raw.tags.includes('valid_qgis')"
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-missing-project"
                    ><v-icon color="#fb8c0087" size="20">warning</v-icon></span
                  >
                </template>
                <span>Missing QGIS project file</span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <span
                    v-if="item.raw.has_conflict"
                    v-bind="props"
                    style="margin-right: 20px"
                    data-cy="project-form-conflict-file"
                    ><v-icon color="#fb8c0087" size="20">error</v-icon></span
                  >
                </template>
                <span>There is conflict file in project</span>
              </v-tooltip>
            </div>
          </v-list-item>
          <v-divider style="color: black" />
        </v-card>
      </template>
      <template v-slot:footer>
        <div class="text-center">
          <v-pagination
            v-if="showFooter && numberOfItems > options.itemsPerPage"
            v-model="options.page"
            :length="Math.ceil(numberOfItems / options.itemsPerPage)"
            :total-visible="7"
            rounded="circle"
            color="primary"
            @update:model-value="fetchPage"
          ></v-pagination>
        </div>
      </template>
      <template #no-data>No projects found</template>
    </v-data-iterator>
  </div>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import { defineComponent, PropType } from 'vue'

import { PaginatedGridOptions } from '@/common'
import { formatToTitle } from '@/common/text_utils'
import { ProjectListItem, VDataIteratorOptions } from '@/modules/project/types'

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
      options: { ...this.initialOptions },
      searchFilterByProjectName: '',
      searchFilterByNamespace: '',
      searchFilterByDay: '',
      loading: false,
      keys: ['name', 'updated', 'disk_usage']
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
        return { title: formatToTitle(i), value: i }
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
    paginating(options: PaginatedGridOptions) {
      this.options = options
    },
    onUpdateOptions(options: VDataIteratorOptions) {
      this.options = {
        itemsPerPage: options.itemsPerPage,
        page: options.page,
        sortDesc: options.sortBy[0].order as boolean,
        sortBy: options.sortBy[0].key
      }
      this.fetchProjects()
    },
    fetchPage(page: number) {
      this.options.page = page
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
