<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-layout class="column">
      <v-row>
        <v-col class="pa-0">
          <v-text-field
            class="search"
            placeholder="Find file"
            append-icon="search"
            v-model="searchFilter"
            hide-details
            style="padding-left: 7px; padding-bottom: 10px"
            v-if="searchFilter !== '' || items.length > 0"
          />
        </v-col>
      </v-row>
      <v-data-table
        v-if="
          searchFilter !== '' ||
          items.length ||
          (project && !project.permissions.upload) ||
          filter !== ''
        "
        class="file-table"
        :headers="header"
        :items="items"
        color="primary"
        no-data-text="No files found."
        :items-per-page="itemPerPage"
        :hide-default-footer="items.length <= itemPerPage"
        :options="options"
        v-model="selected"
        item-key="path"
        data-cy="file-browser-table"
      >
        <template #item.name="{ item }">
          <router-link :to="item.link">
            <file-icon :file="item" />
            <span data-cy="file-browser-item">{{ item.name }}</span>
          </router-link>
          <v-spacer />
          <folder-diff v-if="item.diffStats" v-bind="item.diffStats" />
        </template>
        <template #item.mtime="{ value }">
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <template v-if="value">
                  {{ value | timediff }}
                </template>
              </span>
            </template>
            <span>
              <template v-if="value">
                {{ value | datetime }}
              </template>
            </span>
          </v-tooltip>
        </template>
        <template #item.size="{ value }">
          <template v-if="value !== undefined">
            {{ value | filesize }}
          </template>
        </template>
      </v-data-table>
      <v-card v-else style="-webkit-box-shadow: none; box-shadow: none">
        <v-card-title style="padding-left: 0"
          ><strong>
            Well done! The next step is adding some data.
          </strong></v-card-title
        >
        <v-card-text style="padding-left: 0">
          There are two options: <br />
          <br />
          1. Use the Mergin Maps plugin for QGIS to upload data. This is the
          easiest and <strong>recommended</strong> way. See the documentation on
          <a target="_blank" :href="docsLinkManageCreateProject"
            >how to install and use the plugin</a
          >. <br />
          <br />
          2. Drag and drop files from your computer to the lower part of this
          page. This option is convenient if your project files are already
          fully prepared and only need uploading.
        </v-card-text>
      </v-card>
      <v-spacer />
      <file-menu ref="menu" />
    </v-layout>
  </div>
</template>

<script lang="ts">
import difference from 'lodash/difference'
import escapeRegExp from 'lodash/escapeRegExp'
import max from 'lodash/max'
import orderBy from 'lodash/orderBy'
import union from 'lodash/union'
import Path from 'path'
import Vue from 'vue'
import { mapState } from 'vuex'

import { formatDateTime } from '@/common/date_utils'
import { dirname } from '@/common/path_utils'
import { removeAccents } from '@/common/text_utils'
import FileIcon from '@/modules/project/components/FileIcon.vue'
import FileMenu from '@/modules/project/components/FileMenu.vue'
import FolderDiff from '@/modules/project/components/FolderDiff.vue'

export default Vue.extend({
  name: 'FileBrowserView',
  components: { FileIcon, FolderDiff, FileMenu },
  props: {
    namespace: String,
    projectName: String,
    location: {
      type: String,
      default: ''
    },
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      options: {
        rowsPerPage: -1
      },
      itemPerPage: 50,
      sortBy: 'name',
      searchFilter: '',
      filter: '',
      selected: [],
      header: [
        { text: 'Name', value: 'name' },
        { text: 'Modified', value: 'mtime' },
        { text: 'Size', value: 'size' }
      ]
    }
  },
  computed: {
    ...mapState('instanceModule', ['configData']),
    ...mapState('projectModule', ['project', 'uploads']),
    docsLinkManageCreateProject() {
      return `${this.configData?.docs_url ?? ''}/manage/create-project`
    },
    upload() {
      return this.uploads[this.project.path]
    },
    projectFiles() {
      let files = this.project.files
      if (this.upload && this.diff) {
        files = { ...files, ...this.upload.files }
      }
      return Object.values(files).map(this.fileTreeView)
    },
    directoryFiles() {
      return this.projectFiles.filter(
        (file) => dirname(file.path) === this.location
      )
    },
    folders() {
      const folders = {}
      const prefix = this.location ? escapeRegExp(this.location + '/') : ''
      const regex = new RegExp(`^${prefix}([^/]+)/`)
      this.projectFiles.forEach((f) => {
        const m = f.path.match(regex)
        if (m) {
          const name = m[1]
          if (folders[name]) {
            folders[name].push(f)
          } else {
            folders[name] = [f]
          }
        }
      })
      return Object.keys(folders)
        .sort()
        .map((name) => {
          const path = Path.join(this.location, name)
          const files = folders[name]
          return {
            name,
            path,
            files,
            type: 'folder',
            link: this.folderLink(path),
            size: files.reduce((sum, f) => sum + f.size, 0),
            mtime: max(files, (f) => f.mtime).mtime, // new Date(f.mtime).getTime(),
            flags: this.folderFlags(files),
            diffStats: this.diff ? this.folderDiffStats(files) : null
          }
        })
    },
    diffsList() {
      const list = []
      if (this.diff) {
        const { added, removed, updated } = this.diff
        list.push(
          ...orderBy(
            removed
              .map((path) => this.project.files[path])
              .map(this.fullPathView),
            this.sortBy,
            this.options.descending ? 'desc' : 'asc'
          )
        )
        list.push(
          ...orderBy(
            added.map((path) => this.upload.files[path]).map(this.fullPathView),
            this.sortBy,
            this.options.descending ? 'desc' : 'asc'
          )
        )
        list.push(
          ...orderBy(
            updated
              .map((path) => this.upload.files[path])
              .map(this.fullPathView),
            this.sortBy,
            this.options.descending ? 'desc' : 'asc'
          )
        )
      }
      return list
    },
    items() {
      if (this.filter === 'diff') {
        const changedFiles = this.filterByLocation(this.diffsList)
        if (this.searchFilter) {
          const regex = new RegExp(
            escapeRegExp(removeAccents(this.searchFilter)),
            'i'
          )
          return changedFiles.filter((f) => f.path.search(regex) !== -1)
        }
        return changedFiles
      }
      if (this.searchFilter) {
        const regex = new RegExp(
          escapeRegExp(removeAccents(this.searchFilter)),
          'i'
        )
        return orderBy(
          this.filterByLocation(this.projectFiles).filter(
            (f) => f.path.search(regex) !== -1
          ),
          this.sortBy,
          this.options.descending ? 'desc' : 'asc'
        )
      }
      const items = []
      if (this.location) {
        items.push({
          name: '..',
          type: 'folder',
          link: Path.normalize(Path.join(this.$route.path, '@/')),
          mtime: ''
        })
      }
      items.push(
        ...orderBy(
          this.folders,
          this.sortBy,
          this.options.descending ? 'desc' : 'asc'
        )
      )
      items.push(
        ...orderBy(
          this.directoryFiles,
          this.sortBy,
          this.options.descending ? 'desc' : 'asc'
        )
      )
      return items
    },
    diff() {
      const diff = this.upload && this.upload.diff
      if (diff && diff.changes) {
        return {
          ...diff
        }
      }
      return null
    },
    allSelected() {
      return this.items.every((i) => this.selected.includes(i.path))
    }
  },
  methods: {
    fileFlags(file) {
      return (
        this.diff && {
          added: this.diff.added.includes(file.path),
          updated: this.diff.updated.includes(file.path),
          removed: this.diff.removed.includes(file.path)
        }
      )
    },
    folderFlags(files) {
      // TODO: or use file.flags ?
      return (
        this.diff && {
          added: files.every((f) => this.diff.added.includes(f.path)),
          removed: files.every((f) => this.diff.removed.includes(f.path))
        }
      )
    },
    folderDiffStats(files) {
      const { added, removed, updated } = this.diff
      return {
        added: files.filter((f) => added.includes(f.path)).length,
        removed: files.filter((f) => removed.includes(f.path)).length,
        updated: files.filter((f) => updated.includes(f.path)).length,
        count: files.length
      }
    },
    fullPathView(file) {
      return {
        ...file,
        name: file.path,
        link: this.fileLink(file),
        mtime: formatDateTime(file.mtime),
        flags: this.fileFlags(file)
      }
    },
    fileTreeView(file) {
      const filename = Path.basename(file.path)
      return {
        ...file,
        type: 'file',
        name: filename,
        link: this.fileLink(file),
        mtime: formatDateTime(file.mtime),
        flags: this.fileFlags(file)
      }
    },
    fileLink(file) {
      return `/projects/${this.namespace}/${
        this.projectName
      }/blob/${encodeURIComponent(file.path)}`
    },
    folderLink(path) {
      return `/projects/${this.namespace}/${this.projectName}/tree/${path}`
    },
    filterByLocation(files) {
      let dirPrefix = ''
      if (this.location) {
        dirPrefix = this.location.replace(/\/$/, '') + '/'
        files = files.filter((file) =>
          (dirname(file.path) + '/').startsWith(dirPrefix)
        )
      }
      return files.map((f) => ({ ...f, name: f.path.slice(dirPrefix.length) }))
    },
    openMenu(evt, file) {
      // TODO: highlight
      this.$refs.menu.open(evt, file)
    },
    toggleAll(selected) {
      const fn = selected ? union : difference
      this.selected = fn(
        this.selected,
        this.items.map((i) => i.path)
      )
    },
    changeSort(column) {
      if (this.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.sortBy = column
        this.options.descending = false
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.search {
  max-width: 260px;
  margin: 0 0.25em;
}

.v-menu__content {
  .v-list__tile__title {
    text-align: right;
  }
}

::v-deep .v-data-table {
  tr {
    color: #555;

    &.updated {
      color: orange;
    }

    &.removed,
    &.rmoved {
      color: red;
    }

    &.added,
    &.nmoved {
      color: green;
    }

    a,
    .v-icon {
      color: inherit;
    }

    .v-icon {
      opacity: 0.75;
    }
  }

  td {
    text-align: left;

    a {
      text-decoration: none;

      .v-icon {
        line-height: 18px;
        margin-right: 4px;
      }
    }
  }

  th,
  tr {
    min-width: 0;

    .v-input--checkbox {
      opacity: 0.75;
      align-items: flex-end;
      justify-content: flex-end;

      .v-input--selection-controls__input {
        margin: 0;
      }

      .v-icon {
        pointer-events: none;
      }
    }
  }
}

.v-speed-dial {
  position: absolute;
}

.v-data-table {
  ::v-deep .v-data-footer__select {
    display: none;
  }
}
</style>
