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
        v-if="options && numberOfItems > options.itemsPerPage"
        v-model="options.page"
        :length="Math.ceil(numberOfItems / options.itemsPerPage)"
        :total-visible="7"
        circle
        color="primary"
        @input="fetchPage"
      ></v-pagination>
    </div>
    <v-data-table
      :headers="headers"
      :items="versions"
      :options="options"
      :server-items-length="numberOfItems"
      v-on:update:options="paginating"
      :hide-default-footer="true"
      :loading="loading"
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
              <span v-on="on">{{ item.created | timediff }}</span>
            </template>
            <span>{{ item.created | datetime }}</span>
          </v-tooltip>
        </span>
      </template>
      <template v-slot:item.name="{ item }">
        <span data-cy="project-versions-version">
          <router-link
            :to="{
              name: 'project-versions-detail',
              params: { version_id: item.name, version: item }
            }"
          >
            {{ item.name }}
          </router-link>
        </span>
      </template>
      <template v-slot:item.changes.added="{ item }">
        <span>
          <span class="green--text">{{ item.changes.added.length }}</span>
        </span>
      </template>
      <template v-slot:item.changes.removed="{ item }">
        <span>
          <span class="red--text">{{ item.changes.removed.length }}</span>
        </span>
      </template>
      <template v-slot:item.changes.updated="{ item }">
        <span>
          <span class="orange--text">{{ item.changes.updated.length }}</span>
        </span>
      </template>
      <template v-slot:item.project_size="{ item }">
        {{ item.project_size | filesize }}
      </template>
      <template v-slot:item.archived="{ item }">
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              v-on="on"
              data-cy="project-versions-download-btn"
              @click="
                downloadArchive(
                  '/v1/project/download/' +
                    namespace +
                    '/' +
                    projectName +
                    '?version=' +
                    item.name +
                    '&format=zip'
                )
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
        v-if="options && numberOfItems > options.itemsPerPage"
        v-model="options.page"
        :length="Math.ceil(numberOfItems / options.itemsPerPage)"
        :total-visible="7"
        circle
        color="primary"
        @input="fetchPage"
      ></v-pagination>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions, mapState } from 'vuex'

import MerginAPIMixin from '@/common/mixins/MerginAPIMixin'

export default Vue.extend({
  name: 'ProjectVersionsView',
  mixins: [MerginAPIMixin],
  props: {
    projectName: String,
    namespace: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      dialog: false,
      versions: [],
      numberOfItems: 0,
      options: {
        sortDesc: [true],
        itemsPerPage: 50,
        page: 1
      }
    }
  },
  computed: {
    ...mapState('projectModule', ['project']),
    headers() {
      return [
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
      ]
    }
  },
  watch: {
    $route: 'fetchVersions'
  },
  methods: {
    ...mapActions('projectModule', ['fetchProjectVersions']),
    paginating(options) {
      this.options = options
      this.fetchVersions()
    },
    fetchPage(number) {
      this.options.page = number
      this.fetchVersions()
    },
    onFetchVersionsSuccess(responseData) {
      this.versions = responseData.versions
      this.numberOfItems = responseData.count
      this.loading = false
    },
    fetchVersions() {
      this.loading = true
      const params = {} as any
      params.page = this.options.page
      params.per_page = this.options.itemsPerPage
      params.descending = this.options.sortDesc[0]
      this.fetchProjectVersions({
        params,
        namespace: this.namespace,
        projectName: this.projectName,
        cbSuccess: this.onFetchVersionsSuccess
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
