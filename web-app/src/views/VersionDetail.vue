# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div v-if="version">
    <portal to="download-button">
      <v-tooltip top>
        <template v-slot:activator="{ on }">
        <v-btn
          icon
          v-on="on"
          :href="downloadUrl"
        >
          <v-icon>archive</v-icon>
        </v-btn>
        </template>
        <span>Download Project Version {{ version.name }} (ZIP)</span>
      </v-tooltip>
    </portal>
    <v-list two-line subheader>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Version</v-list-item-title>
          <v-list-item-subtitle>{{ version.name }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Author</v-list-item-title>
          <v-list-item-subtitle>{{ version.author }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Project Size</v-list-item-title>
          <v-list-item-subtitle>{{ version.project_size | filesize }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Created</v-list-item-title>
          <v-list-item-subtitle>{{ version.created | datetime }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>User Agent</v-list-item-title>
          <v-list-item-subtitle>{{ version.user_agent }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <v-list class="files" expand>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Files changes:</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-group
        v-for="{ key, text, icon } in changeHeader"
        :key="key"
        no-action
      >
<!--                v-if="changes[key].length"-->
<template v-slot:activator>
        <v-list-item-content>
          <v-list-item-title>
            <v-icon small v-text="icon" class="mr-2"/>
            <span>{{ text }} ({{ changes[key].length }})</span>
          </v-list-item-title>
        </v-list-item-content>
</template>

        <div
          class="v-list__tile v-list-item-file"
          v-for="item in changes[key]"
          :key="item.path"
          no-action
        >
          <div :class="colors[key]">
            {{ item.path }}: {{ version.changesets[item.path] ? version.changesets[item.path]['size'] : item.size | filesize }}
            <template
              v-if="version.changesets[item.path]">
              <div v-if="!version.changesets[item.path].error">
                <router-link
                class="show-advanced"
                :to="{
                  name: `${asAdmin ? 'admin-' : ''}file-version-detail`,
                  params: {
                    namespace: version.namespace,
                    projectName: version.project_name,
                    version_id: version.name,
                    path: item.path }}">
                <v-btn>
                  <span>Show advanced</span>
                </v-btn>
                </router-link>
                <file-changeset-summary-table :changesets="version.changesets[item.path]['summary']"/>
              </div>
              <div v-else class="text--primary">
                Details not available: {{ version.changesets[item.path].error }}
              </div>
            </template>
          </div>
        </div>
      </v-list-group>
    </v-list>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import FileChangesetSummaryTable from '../components/FileChangesetSummaryTable'

const Colors = {
  added: 'green--text',
  removed: 'red--text',
  updated: 'orange--text'
}

export default {
  name: 'project-version',
  components: { FileChangesetSummaryTable },
  props: {
    version_id: {
      type: String,
      default: ''
    },
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      version: null
    }
  },
  created () {
    this.getVersion()
  },
  computed: {
    ...mapState(['project']),
    colors () {
      return Colors
    },
    changeHeader () {
      return [
        { key: 'added', text: 'Added', icon: 'add_circle' },
        { key: 'removed', text: 'Removed', icon: 'delete' },
        { key: 'updated', text: 'Modified', icon: 'edit' }
      ]
    },
    changes () {
      return this.version && this.version.changes
    },
    downloadUrl () {
      return this.$http.absUrl(`/v1/project/download/${this.project.namespace}/${this.project.name}?version=${this.version_id}&format=zip`)
    }
  },
  watch: {
    $route: 'getVersion'
  },
  methods: {
    getVersion () {
      if (!this.project.versions) {
        this.$http.get(`/v1/project/version/${this.project.namespace}/${this.project.name}?version_id=${this.version_id}`)
          .then(resp => {
            if (resp.data.length) {
              const version = resp.data[0]
              version.changes = resp.data[0].changes
              this.version = version
            }
          })
          .catch(err => {
            const msg = (err.response) ? err.response.data.detail : 'Failed to fetch project version'
            this.$notification.error(msg)
          })
      } else {
        this.version = this.project.versions.find(v => v.name === this.version_id)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.status {
  margin: 0.5em auto;
  padding: 0 1em;
  text-align: center;
  color: #fff;
  height: 2em;
  line-height: 2em;
  border-radius: 1em;
  float: right;
}

.v-list-item-file {
  min-height: 48px;
  height: auto;
}

.v-list {
  ::v-deep .v-list-item {
    font-size: 14px;
    color: #444;
    .v-list-item__title {
      font-weight: 500;
    }
  }

  &.files {
    ::v-deep .v-list-group__items {
      .v-list-item {
        padding-left: 20px;
      }
    }
  }
}
.show-advanced {
  font-style: unset;
  button {
    font-size: 12px;
    margin-left: 30px;
  }
}
</style>
