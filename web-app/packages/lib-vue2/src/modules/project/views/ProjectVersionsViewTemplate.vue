<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-layout align-center shrink>
      <v-spacer />
    </v-layout>
    <div class="text-center">
      <v-pagination
        v-if="showPagination && options && versionsCount > options.itemsPerPage"
        v-model="options.page"
        :length="Math.ceil(versionsCount / options.itemsPerPage)"
        :total-visible="2"
        circle
        color="primary"
        @input="fetchPage"
      ></v-pagination>
    </div>
    <v-data-table
      :headers="headers"
      :items="items"
      item-key="name"
      :options="options"
      :server-items-length="versionsCount"
      v-on:update:options="paginating"
      :hide-default-footer="true"
      :loading="versionsLoading"
      no-data-text="No project history"
      color="primary"
      data-cy="project-verision-table"
    >
      <!-- headers -->
      <template v-slot:header.changes.added="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Added</span>
        </v-tooltip>
      </template>
      <template v-slot:header.changes.removed="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Deleted</span>
        </v-tooltip>
      </template>
      <template v-slot:header.changes.updated="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Modified</span>
        </v-tooltip>
      </template>
      <!-- data -->
      <template v-slot:item.created="{ item }">
        <span>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span :style="[rowStyle(item)]" v-on="on">{{
                item.created | timediff
              }}</span>
            </template>
            <span>{{ item.created | datetime }}</span>
          </v-tooltip>
        </span>
      </template>
      <template v-slot:item.author="{ item }"
        ><span :style="[rowStyle(item)]">{{ item.author }}</span></template
      >
      <template v-slot:item.name="{ item }">
        <span data-cy="project-versions-version">
          <router-link
            :style="[rowStyle(item)]"
            :to="
              item.disabled
                ? ''
                : {
                    name: 'project-versions-detail',
                    params: { version_id: item.name }
                  }
            "
          >
            {{ item.name }}
          </router-link>
        </span>
      </template>
      <template v-slot:item.changes.added="{ item }">
        <span>
          <span :style="[rowStyle(item)]" class="green--text">{{
            item.changes.added.length
          }}</span>
        </span>
      </template>
      <template v-slot:item.changes.removed="{ item }">
        <span>
          <span :style="[rowStyle(item)]" class="red--text">{{
            item.changes.removed.length
          }}</span>
        </span>
      </template>
      <template v-slot:item.changes.updated="{ item }">
        <span>
          <span :style="[rowStyle(item)]" class="orange--text">{{
            item.changes.updated.length
          }}</span>
        </span>
      </template>
      <template v-slot:item.project_size="{ item }">
        <span :style="[rowStyle(item)]">{{
          item.project_size | filesize
        }}</span>
      </template>
      <template v-slot:item.archived="{ item }">
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              v-on="on"
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
            >
              <v-icon>archive</v-icon>
            </v-btn>
          </template>
          <span>Download Project Version {{ item.name }} (ZIP)</span>
        </v-tooltip>
      </template>
    </v-data-table>
    <div class="text-center">
      <v-pagination
        v-if="showPagination && options && versionsCount > options.itemsPerPage"
        v-model="options.page"
        :length="Math.ceil(versionsCount / options.itemsPerPage)"
        :total-visible="7"
        circle
        color="primary"
        @input="fetchPage"
      ></v-pagination>
    </div>
    <slot name="table-footer"></slot>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent, PropType } from 'vue'

import {
  FetchProjectVersionsParams,
  ProjectVersion,
  ProjectVersionsItem
} from '@/modules'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'ProjectVersionsViewTemplate',
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
      headers: [
        { text: 'Version', value: 'name' },
        { text: 'Created', value: 'created' },
        { text: 'Author', value: 'author', sortable: false },
        {
          text: 'Added',
          value: 'changes.added',
          icon: 'add_circle',
          color: 'green',
          sortable: false
        },
        {
          text: 'Removed',
          value: 'changes.removed',
          icon: 'delete',
          color: 'red',
          sortable: false
        },
        {
          text: 'Modified',
          value: 'changes.updated',
          icon: 'edit',
          color: 'orange',
          sortable: false
        },
        { text: 'Size', value: 'project_size', sortable: false },
        { text: '', value: 'archived', sortable: false }
      ],
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
  watch: {
    $route: 'fetchVersions'
  },
  methods: {
    ...mapActions(useProjectStore, ['fetchProjectVersions', 'downloadArchive']),
    paginating(options) {
      this.options = options
      this.fetchVersions()
    },
    fetchPage(number) {
      this.options.page = number
      this.fetchVersions()
    },
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
    }
  }
})
</script>

<style lang="scss" scoped>
.v-card.table {
  min-height: unset;
  overflow: unset;
}

.changes {
  flex: 0.3 1 auto;
}
</style>
