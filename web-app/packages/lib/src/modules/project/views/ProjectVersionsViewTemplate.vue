<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section ground class="flex justify-content-end">
      <AppMenu :items="filterMenuItems" />
    </app-section>
    <app-section>
      <project-versions-table
        :project-name="projectName"
        :namespace="namespace"
        :disabled-keys="disabledKeys"
        :show-pagination="showPagination"
        v-model:options="options"
        @row-click="rowClick"
      />
      <slot name="table-footer"></slot>
    </app-section>
    <VersionDetailSidebar />
  </app-container>
</template>

<script lang="ts">
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { defineComponent, PropType } from 'vue'

import VersionDetailSidebar from '../components/VersionDetailSidebar.vue'

import { AppSection, AppContainer } from '@/common/components'
import AppMenu from '@/common/components/AppMenu.vue'
import { DataViewWrapperOptions } from '@/common/components/data-view/types'
import { ProjectVersionsTable } from '@/modules'

export default defineComponent({
  name: 'ProjectVersionsViewTemplate',
  components: {
    AppSection,
    AppContainer,
    VersionDetailSidebar,
    AppMenu,
    ProjectVersionsTable
  },
  props: {
    projectName: String,
    namespace: String,
    /** Default items per page */
    defaultItemsPerPage: Number as PropType<number>,
    /** Disabled keys (name attribute of rows in vuetify table are keys for items) */
    disabledKeys: { type: Array as PropType<string[]>, default: () => [] },
    /** Show pagination */
    showPagination: { type: Boolean, default: true }
  },
  data() {
    return {
      options: {
        sortDesc: true,
        itemsPerPage: this.defaultItemsPerPage ?? 50,
        page: 1
      } as DataViewWrapperOptions
    }
  },
  computed: {
    filterMenuItems(): MenuItem[] {
      return [
        {
          label: 'Newest versions',
          key: 'newest',
          sortDesc: true
        },
        {
          label: 'Oldest versions',
          key: 'oldest',
          sortDesc: false
        }
      ].map((item) => ({
        ...item,
        command: (e: MenuItemCommandEvent) => this.menuItemClick(e),
        class: this.options.sortDesc === item.sortDesc ? 'bg-primary-400' : ''
      }))
    }
  },
  methods: {
    rowClick(item) {
      this.$router.push({
        query: {
          version_id: item.name
        }
      })
    },
    menuItemClick(e: MenuItemCommandEvent) {
      this.options.sortDesc = e.item.sortDesc
    }
  }
})
</script>

<style lang="scss" scoped></style>
