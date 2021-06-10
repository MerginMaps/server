# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-layout class="column">
      <v-row>
       <v-text-field
        class="search"
        placeholder="Find file"
        append-icon="search"
        v-model="searchFilter"
        hide-details
        style="padding-left: 7px; padding-bottom: 10px;"
        v-if="items.length > 0"
      />
        </v-row>
      <v-data-table
        v-if="items.length  || !project.permissions.upload || filter !== ''"
        class="file-table"
        :headers="header"
        :items="items"
        color="primary"
        no-data-text="Empty project."
        :items-per-page="itemPerPage"
        :hide-default-footer="items.length <= itemPerPage"
        :options="options"
        v-model="selected"
        item-key="path"
      >
        <template v-slot:item="{ item }">
        <tr >
          <td>
            <router-link :to="item.link">
              <file-icon :file="item"/>
              <span>{{ item.name }}</span>
              <small
                v-if="item.flags && (item.flags.rmoved || item.flags.nmoved)"
                class="ml-1"
              >
                [renamed]
              </small>
            </router-link>
            <v-spacer/>
            <folder-diff
              v-if="item.diffStats"
              v-bind="item.diffStats"
            />
          </td>
          <td>
            <v-tooltip bottom>
              <template v-slot:activator="{ on }">
                <span v-on="on">
                  <template v-if="item.mtime">
                    {{ item.mtime | timediff }}
                  </template>
                </span>
              </template>
              <span>
                  <template v-if="item.mtime">
                    {{ item.mtime | datetime }}
                  </template>
              </span>
            </v-tooltip>
          </td>
          <td>
            <template v-if="item.size !== undefined">
              {{ item.size | filesize }}
            </template>
          </td>
        </tr>
        </template>
      </v-data-table>
      <v-card v-else
      style="-webkit-box-shadow: none; box-shadow: none;">
        <v-card-title style="padding-left: 0px;"><strong> Well done! The next step is adding some data. </strong></v-card-title>
        <v-card-text style="padding-left: 0px;">
          There are two options: <br> <br>
          1. Use the Mergin plugin for QGIS to upload data. This is the easiest and <strong>recommended</strong> way. See the documentation on <a target="_blank" href="https://help.cloudmergin.com/working-with-qgis-plugin">how to install and use the plugin</a>. <br> <br>
          2. Drag and drop files from your computer to the lower part of this page. This option is convenient if your project files are already fully prepared and only need uploading.
        </v-card-text>
      </v-card>
      <v-spacer/>
      <file-menu ref="menu"/>
    </v-layout>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import Path from 'path'
import escapeRegExp from 'lodash/escapeRegExp'
import orderBy from 'lodash/orderBy'
import max from 'lodash/max'
import union from 'lodash/union'
import difference from 'lodash/difference'

import { dirname, formatDateTime, removeAccents } from '@/util'
import FolderDiff from '@/components/FolderDiff'
import FileMenu from '@/components/FileMenu'
import FileIcon from '@/components/FileIcon'

export default {
  name: 'file-browser',
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
  data () {
    return {
      options: {
        rowsPerPage: -1
      },
      itemPerPage: 50,
      sortBy: 'name',
      searchFilter: '',
      filter: '',
      selected: [],
      header: [{ text: 'Name', value: 'name' },
        { text: 'Modified', value: 'mtime' },
        { text: 'Size', value: 'size' }]
    }
  },
  computed: {
    ...mapState(['project', 'uploads']),
    upload () {
      return this.uploads[this.project.path]
    },
    projectFiles () {
      let files = this.project.files
      if (this.upload && this.diff) {
        files = { ...files, ...this.upload.files }
      }
      return Object.values(files).map(this.fileTreeView)
    },
    directoryFiles () {
      return this.projectFiles.filter(file => dirname(file.path) === this.location)
    },
    folders () {
      const folders = {}
      const prefix = this.location ? escapeRegExp(this.location + '/') : ''
      const regex = new RegExp(`^${prefix}([^/]+)/`)
      this.projectFiles.forEach(f => {
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
      return Object.keys(folders).sort().map(name => {
        const path = Path.join(this.location, name)
        const files = folders[name]
        return {
          name,
          path,
          files,
          type: 'folder',
          link: this.folderLink(path),
          size: files.reduce((sum, f) => sum + f.size, 0),
          mtime: max(files, f => f.mtime).mtime, // new Date(f.mtime).getTime(),
          flags: this.folderFlags(files),
          diffStats: this.diff ? this.folderDiffStats(files) : null
        }
      })
    },
    diffsList () {
      const list = []
      if (this.diff) {
        const { added, removed, updated, moved } = this.diff
        list.push(...orderBy(moved.map(item => this.project.files[item.path]).map(this.fullPathView), this.sortBy, this.options.descending ? 'desc' : 'asc'))
        list.push(...orderBy(moved.map(item => this.upload.files[item.new_path]).map(this.fullPathView), this.sortBy, this.options.descending ? 'desc' : 'asc'))
        list.push(...orderBy(removed.map(path => this.project.files[path]).map(this.fullPathView), this.sortBy, this.options.descending ? 'desc' : 'asc'))
        list.push(...orderBy(added.map(path => this.upload.files[path]).map(this.fullPathView), this.sortBy, this.options.descending ? 'desc' : 'asc'))
        list.push(...orderBy(updated.map(path => this.upload.files[path]).map(this.fullPathView), this.sortBy, this.options.descending ? 'desc' : 'asc'))
      }
      return list
    },
    items () {
      if (this.filter === 'diff') {
        const changedFiles = this.filterByLocation(this.diffsList)
        if (this.searchFilter) {
          const regex = new RegExp(escapeRegExp(removeAccents(this.searchFilter)), 'i')
          return changedFiles.filter(f => f.path.search(regex) !== -1)
        }
        return changedFiles
      }
      if (this.searchFilter) {
        const regex = new RegExp(escapeRegExp(removeAccents(this.searchFilter)), 'i')
        return orderBy(this.filterByLocation(this.projectFiles).filter(f => f.path.search(regex) !== -1), this.sortBy, this.options.descending ? 'desc' : 'asc')
      }
      const items = []
      if (this.location) {
        items.push({
          name: '..',
          type: 'folder',
          link: Path.normalize(Path.join(this.$route.path, '../')),
          mtime: ''
        })
      }
      items.push(...orderBy(this.folders, this.sortBy, this.options.descending ? 'desc' : 'asc'))
      items.push(...orderBy(this.directoryFiles, this.sortBy, this.options.descending ? 'desc' : 'asc'))
      return items
    },
    diff () {
      const diff = this.upload && this.upload.diff
      if (diff && diff.changes) {
        return {
          ...diff,
          renamedOriginal: diff.moved.map(f => f.path),
          renamedNew: diff.moved.map(f => f.new_path)
        }
      }
      return null
    },
    allSelected () {
      return this.items.every(i => this.selected.includes(i.path))
    }
  },
  methods: {
    fileFlags (file) {
      return this.diff && {
        added: this.diff.added.includes(file.path),
        updated: this.diff.updated.includes(file.path),
        removed: this.diff.removed.includes(file.path),
        rmoved: this.diff.renamedOriginal.includes(file.path), // this.diff.moved.find(f => f.path === file.path),
        nmoved: this.diff.renamedNew.includes(file.path) // this.diff.moved.find(f => f.new_path === file.path)
      }
    },
    folderFlags (files) {
      // TODO: or use file.flags ?
      return this.diff && {
        added: files.every(f => this.diff.added.includes(f.path)),
        removed: files.every(f => this.diff.removed.includes(f.path)),
        // updated: files.some(f => updated.includes(f.path) || removed.includes(f.path) || added.includes(f.path))
        rmoved: files.every(f => this.diff.renamedOriginal.includes(f.path)),
        nmoved: files.every(f => this.diff.renamedNew.includes(f.path))
      }
    },
    folderDiffStats (files) {
      const { added, removed, updated, moved } = this.diff
      return {
        added: files.filter(f => added.includes(f.path)).length,
        removed: files.filter(f => removed.includes(f.path)).length,
        updated: files.filter(f => updated.includes(f.path) || moved.find(f2 => f2.path === f.path || f2.new_path === f.path)).length,
        count: files.length
      }
    },
    fullPathView (file) {
      return {
        ...file,
        name: file.path,
        link: this.fileLink(file),
        mtime: formatDateTime(file.mtime),
        flags: this.fileFlags(file)
      }
    },
    fileTreeView (file) {
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
    fileLink (file) {
      return `${this.asAdmin ? '/admin' : ''}/projects/${this.namespace}/${this.projectName}/blob/${encodeURIComponent(file.path)}`
    },
    folderLink (path) {
      return `/projects/${this.namespace}/${this.projectName}/tree/${path}`
    },
    filterByLocation (files) {
      let dirPrefix = ''
      if (this.location) {
        dirPrefix = this.location.replace(/\/$/, '') + '/'
        files = files.filter(file => (dirname(file.path) + '/').startsWith(dirPrefix))
      }
      return files.map(f => ({ ...f, name: f.path.slice(dirPrefix.length) }))
    },
    openMenu (evt, file) {
      // TODO: highlight
      this.$refs.menu.open(evt, file)
    },
    toggleAll (selected) {
      const fn = selected ? union : difference
      this.selected = fn(this.selected, this.items.map(i => i.path))
    },
    changeSort (column) {
      if (this.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.sortBy = column
        this.options.descending = false
      }
    }
  }
}
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

    &.removed, &.rmoved {
      color: red;
    }

    &.added, &.nmoved {
      color: green;
    }

    a, .v-icon {
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
  th, tr {
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
