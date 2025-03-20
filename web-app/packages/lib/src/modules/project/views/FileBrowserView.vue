<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <!-- Searching -->
    <app-container
      v-if="searchFilter !== '' || Object.keys(project?.files ?? {}).length > 0"
    >
      <app-section ground>
        <div class="flex align-items-center">
          <span class="p-input-icon-left flex-grow-1">
            <i class="ti ti-search paragraph-p3"></i>
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

    <app-container v-if="dataTableOpen && projectName">
      <app-section>
        <files-table
          :project-name="projectName"
          :namespace="namespace"
          :location="location"
          :options="options"
          :search="searchFilter"
          @row-click="rowClick"
        />
      </app-section>
    </app-container>
    <app-container
      v-if="project && $route.name === 'project-tree' && isProjectWriter"
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

            <h4 class="title-t1 text-color-forest">
              Mergin Maps plugin for QGIS
            </h4>
            <p class="paragraph-p6 opacity-80 m-0">
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
    <!-- Sidebars -->
    <file-detail-sidebar :namespace="namespace" :project-name="projectName" />
    <!-- notifications -->
    <upload-progress />
  </div>
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { defineComponent } from 'vue'

import {
  AppSection,
  AppContainer,
  AppPanelToggleable
} from '@/common/components'
import AppMenu from '@/common/components/AppMenu.vue'
import { useInstanceStore } from '@/modules/instance/store'
import DropArea from '@/modules/project/components/DropArea.vue'
import FileDetailSidebar from '@/modules/project/components/FileDetailSidebar.vue'
import FilesTable from '@/modules/project/components/FilesTable.vue'
import UploadProgress from '@/modules/project/components/UploadProgress.vue'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'FileBrowserView',
  components: {
    FilesTable,
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
    }
  },
  data() {
    return {
      options: {
        sortBy: 'name',
        sortDesc: 1
      },
      searchFilter: ''
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    ...mapState(useProjectStore, ['project', 'uploads', 'isProjectWriter']),
    docsLinkManageCreateProject() {
      return `${this.configData?.docs_url ?? ''}/manage/create-project`
    },
    dataTableOpen() {
      return !!(
        this.searchFilter !== '' ||
        Object.keys(this.project.files ?? {}).length ||
        (this.project && !this.isProjectWriter)
      )
    },
    filterMenuItems(): MenuItem[] {
      return [
        {
          label: 'Sort by name A-Z',
          key: 'name',
          sortDesc: 1
        },
        {
          label: 'Sort by name Z-A',
          key: 'name',
          sortDesc: -1
        },
        {
          label: 'Sort by last modified',
          key: 'mtime',
          sortDesc: -1
        },
        {
          label: 'Sort by file size',
          key: 'size',
          sortDesc: -1
        }
      ].map((item) => ({
        ...item,
        command: (e: MenuItemCommandEvent) => this.menuItemClick(e),
        class:
          this.options.sortBy === item.key &&
          this.options.sortDesc === item.sortDesc
            ? 'bg-primary-400'
            : ''
      }))
    }
  },
  methods: {
    rowClick(file) {
      this.$router.push({ path: file.link })
    },
    menuItemClick(e: MenuItemCommandEvent) {
      this.options.sortBy = e.item.key
      this.options.sortDesc = e.item.sortDesc
    }
  }
})
</script>

<style lang="scss" scoped></style>
