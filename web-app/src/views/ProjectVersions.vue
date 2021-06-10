# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-layout align-center shrink>
      <v-spacer/>
    </v-layout>
    <v-data-table
      :headers="headers"
      :items="versions"
      no-data-text="No project history"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="versions.length <= 10"
      :options="options"
    >
      <!-- headers -->
      <template v-slot:header.changes.added="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
             <v-icon v-on="on" small :color="header.color">{{ header.icon }}</v-icon>
          </template>
          <span>Added</span>
        </v-tooltip>
      </template>
      <template v-slot:header.changes.removed="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
             <v-icon v-on="on" small :color="header.color">{{ header.icon }}</v-icon>
          </template>
          <span>Deleted</span>
        </v-tooltip>
      </template>
      <template v-slot:header.changes.updated="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
             <v-icon v-on="on" small :color="header.color">{{ header.icon }}</v-icon>
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
           <span>
             <router-link :to="{name: `${asAdmin ? 'admin-' : ''}project-versions-detail`, params: {version_id: item.name, version: item}}">
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
            :href="'/v1/project/download/' + namespace + '/'+ projectName +'?version=' + item.name + '&format=zip'"
          >
            <v-icon>archive</v-icon>
          </v-btn>
            </template>
          <span>Download Project Version {{ item.name }} (ZIP)</span>
        </v-tooltip>
     </template>
    </v-data-table>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'project-versions',
  props: {
    projectName: String,
    namespace: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      dialog: false,
      versions: [],
      options: {
        'sort-by': 'version'
      }
    }
  },
  computed: {
    ...mapState(['project']),
    headers () {
      return [
        { text: 'Version', value: 'name' },
        { text: 'Created', value: 'created' },
        { text: 'Author', value: 'author' },
        { text: 'Added', value: 'changes.added', icon: 'add_circle', color: 'green' },
        { text: 'Removed', value: 'changes.removed', icon: 'delete', color: 'red' },
        { text: 'Modified', value: 'changes.updated', icon: 'edit', color: 'orange' },
        { text: 'Size', value: 'project_size' },
        { text: '', value: 'archived' }
      ]
    }
  },
  created () {
    this.fetchVersions()
  },
  watch: {
    $route: 'fetchVersions'
  },
  methods: {
    fetchVersions () {
      this.$http.get(`/v1/project/version/${this.namespace}/${this.projectName}`)
        .then(resp => {
          this.versions = resp.data
          this.$store.commit('projectVersions', { project: this.project, versions: this.versions })
        })
        .catch(() => {
          this.$notification.error('Failed to fetch project versions')
        })
    }
  }
}
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
