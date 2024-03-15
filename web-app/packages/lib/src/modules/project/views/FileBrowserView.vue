<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <!-- Searching -->
    <app-container v-if="searchFilter !== '' || items.length > 0">
      <app-section ground>
        <div class="flex align-items-center">
          <span class="p-input-icon-left flex-grow-1">
            <i class="ti ti-search text-xl"></i>
            <PInputText
              placeholder="Search files"
              data-cy="search-files-field"
              v-model="searchFilter"
              class="w-full"
            />
          </span>
          <AppMenu :items="filterMenuItems" />
        </div>
      </app-section>
    </app-container>

    <app-container
      v-if="
        project &&
        $route.name === 'project-tree' &&
        project.permissions &&
        project.permissions.upload
      "
    >
      <app-panel-toggleable :collapsed="dataTableOpen">
        <template #title>Upload files</template>
        <div class="flex flex-column lg:flex-row">
          <div
            class="flex flex-column text-center align-items-center w-12 lg:w-6 mb-4 lg:mb-0 lg:mr-4 border-round-xl surface-ground p-4 row-gap-3"
          >
            <div class="w-full flex justify-content-end mb-0">
              <PTag>Recommended</PTag>
            </div>

            <div
              class="flex align-items-center justify-content-center text-2xl surface-section border-circle p-4 text-color-forest w-5rem h-5rem"
            >
              <img src="@/assets/Icon/24/QGIS.svg" width="24" height="24" />
            </div>

            <h4 class="text-lg font-semibold text-color-forest">
              Mergin Maps plugin for QGIS
            </h4>
            <p class="text-sm opacity-80 m-0">
              This is the easiest and recommended way.
              <a
                target="_blank"
                class="text-color-forest font-semibold no-underline"
                :href="docsLinkManageCreateProject"
                >Learn how to use it.</a
              >
            </p>
          </div>
          <div class="w-12 lg:w-6 border-round-xl surface-ground">
            <drop-area :location="location" data-cy="project-drop-area">
            </drop-area>
          </div>
        </div>
      </app-panel-toggleable>
    </app-container>

    <app-container v-if="dataTableOpen">
      <app-section>
        <PDataView
          :value="items"
          :data-key="'path'"
          :paginator="items.length > itemPerPage"
          :rows="itemPerPage"
          :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
          data-cy="file-browser-table"
        >
          <template #header>
            <div class="grid grid-nogutter">
              <!-- Visible on lg breakpoint > -->
              <div
                v-for="col in columns"
                :class="[`col-${col.cols ?? 3}`, 'text-xs hidden lg:flex']"
                :key="col.text"
              >
                {{ col.text }}
              </div>
              <!-- else -->
              <div class="col-12 flex lg:hidden">Files</div>
            </div>
          </template>
          <template #list="slotProps">
            <div
              v-for="item in slotProps.items"
              :key="item.id"
              class="grid grid-nogutter px-4 py-3 mt-0 border-bottom-1 border-gray-200 text-xs hover:bg-gray-50 cursor-pointer row-gap-2"
              @click.prevent="rowClick(item.link)"
            >
              <!-- Columns, we are using data view instead table, it is better handling of respnsive state -->
              <div
                v-for="col in columns"
                :class="[
                  `lg:col-${col.cols ?? 3}`,
                  'flex align-items-center col-12'
                ]"
                :key="col.key"
              >
                <span
                  v-if="col.key === 'name'"
                  class="font-semibold mb-2 lg:mb-0 m-0"
                >
                  <file-icon :file="item" />{{ item.name }}
                </span>
                <span
                  v-else-if="col.key === 'mtime'"
                  v-tooltip.bottom="{ value: $filters.datetime(item.mtime) }"
                  class="opacity-80"
                >
                  {{ $filters.timediff(item.mtime) }}
                </span>
                <span v-else class="opacity-80">{{
                  $filters.filesize(item.size)
                }}</span>
              </div>
            </div>
          </template>
          <template #empty>
            <div class="w-full text-center p-4">
              <span>No files found.</span>
            </div>
          </template>
        </PDataView>
      </app-section>
    </app-container>
    <!-- Sidebars -->
    <file-detail-sidebar :namespace="namespace" :project-name="projectName" />
    <!-- notifications -->
    <upload-progress />
  </div>
</template>

<script lang="ts">
import difference from 'lodash/difference'
import escapeRegExp from 'lodash/escapeRegExp'
import max from 'lodash/max'
import orderBy from 'lodash/orderBy'
import union from 'lodash/union'
import Path from 'path'
import { mapState } from 'pinia'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { defineComponent } from 'vue'

import {
  AppSection,
  AppContainer,
  AppPanelToggleable
} from '@/common/components'
import AppMenu from '@/common/components/AppMenu.vue'
import { dirname } from '@/common/path_utils'
import { removeAccents } from '@/common/text_utils'
import { useInstanceStore } from '@/modules/instance/store'
import DropArea from '@/modules/project/components/DropArea.vue'
import FileDetailSidebar from '@/modules/project/components/FileDetailSidebar.vue'
import FileIcon from '@/modules/project/components/FileIcon.vue'
import UploadProgress from '@/modules/project/components/UploadProgress.vue'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'FileBrowserView',
  components: {
    FileIcon,
    AppSection,
    AppContainer,
    AppPanelToggleable,
    DropArea,
    FileDetailSidebar,
    AppMenu,
    UploadProgress
  },
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
        rowsPerPage: -1,
        descending: false,
        sortBy: 'name'
      },
      // Setup this to lower number in case of testing
      itemPerPage: 50,
      searchFilter: '',
      filter: '',
      selected: [],
      columns: [
        { text: 'Name', key: 'name', cols: 6 },
        { text: 'Modified', key: 'mtime' },
        { text: 'Size', key: 'size' }
      ]
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    ...mapState(useProjectStore, ['project', 'uploads']),
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
            this.options.sortBy,
            this.options.descending ? 'desc' : 'asc'
          )
        )
        list.push(
          ...orderBy(
            added.map((path) => this.upload.files[path]).map(this.fullPathView),
            this.options.sortBy,
            this.options.descending ? 'desc' : 'asc'
          )
        )
        list.push(
          ...orderBy(
            updated
              .map((path) => this.upload.files[path])
              .map(this.fullPathView),
            this.options.sortBy,
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
        // TODO: Replace with DataView sorting instead this order_by with lodash
        return orderBy(
          this.filterByLocation(this.projectFiles).filter(
            (f) => f.path.search(regex) !== -1
          ),
          this.options.sortBy,
          this.options.descending ? 'desc' : 'asc'
        )
      }
      const items = []
      if (this.location) {
        items.push({
          name: '..',
          type: 'folder',
          link: Path.normalize(Path.join(this.$route.path, '..')),
          mtime: ''
        })
      }
      items.push(
        ...orderBy(
          this.folders,
          this.options.sortBy,
          this.options.descending ? 'desc' : 'asc'
        )
      )
      items.push(
        ...orderBy(
          this.directoryFiles,
          this.options.sortBy,
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
    },
    dataTableOpen() {
      return !!(
        this.searchFilter !== '' ||
        this.items.length ||
        (this.project && !this.project.permissions.upload) ||
        this.filter !== ''
      )
    },
    filterMenuItems(): MenuItem[] {
      return [
        {
          label: 'Sort by name A-Z',
          key: 'name',
          sortDesc: false
        },
        {
          label: 'Sort by name Z-A',
          key: 'name',
          sortDesc: true
        },
        {
          label: 'Sort by last modified',
          key: 'mtime',
          sortDesc: true
        },
        {
          label: 'Sort by file size',
          key: 'size',
          sortDesc: true
        }
      ].map((item) => ({
        ...item,
        command: (e: MenuItemCommandEvent) => this.menuItemClick(e),
        class:
          this.options.sortBy === item.key &&
          this.options.descending === item.sortDesc
            ? 'bg-primary-400'
            : ''
      }))
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
    toggleAll(selected) {
      const fn = selected ? union : difference
      this.selected = fn(
        this.selected,
        this.items.map((i) => i.path)
      )
    },
    changeSort(column) {
      if (this.options.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.options.sortBy = column
        this.options.descending = false
      }
    },
    rowClick(path: string) {
      this.$router.push({ path })
    },
    menuItemClick(e: MenuItemCommandEvent) {
      this.options.sortBy = e.item.key
      this.options.descending = e.item.sortDesc
    }
  }
})
</script>

<style lang="scss" scoped></style>
