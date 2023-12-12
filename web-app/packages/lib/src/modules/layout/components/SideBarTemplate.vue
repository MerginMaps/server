<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <aside
    :class="[
      'sidebar',
      'fixed',
      'w-full',
      'h-screen',
      'top-0',
      'left-0',
      'overflow-auto',
      'surface-section',
      'transition-all',
      'transition-duration-500',
      !isOpen ? '-translate-x-100' : 'xl:translate-x-0'
    ]"
  >
    <div class="flex flex-column justify-content-between h-screen">
      <div>
        <header>
          <div class="xl:hidden flex justify-content-end">
            <PButton icon="ti ti-x" text rounded @click="onCloseClick" />
          </div>

          <div class="flex justify-content-center p-4">
            <img src="@/assets/mm-logo.svg" />
          </div>
        </header>

        <nav>
          <ul class="list-none p-0 m-0">
            <template v-for="item in initialSidebarItems" :key="item.to">
              <side-bar-item :item="item"></side-bar-item>
            </template>
            <slot name="items">
              <!-- sidebar items -->
            </slot>
          </ul>
        </nav>
      </div>
      <div>
        <slot name="footer">
          <!-- footer content -->
        </slot>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { SideBarItemModel } from '../types'

import SideBarItem from '@/modules/layout/components/SideBarItem.vue'
import { useLayoutStore } from '@/modules/layout/store'

const route = useRoute()
const layoutStore = useLayoutStore()
layoutStore.init()

const currentPage = computed(() => route.name)

const initialSidebarItems = computed<SideBarItemModel[]>(() => {
  return [
    {
      active: currentPage.value === 'dashboard',
      title: 'Dashboard',
      to: '/dashboard',
      icon: 'ti ti-home'
    },
    {
      active: currentPage.value === 'projects',
      title: 'Projects',
      to: '/projects',
      icon: 'ti ti-article'
    }
  ]
})
const isOpen = computed<boolean>(() => layoutStore.drawer)

const onCloseClick = () => {
  layoutStore.setDrawer(false)
}
</script>

<style lang="scss" scoped>
.sidebar {
  // Based on <main> grid values
  max-width: 16.66%;
  // TODO: Clean it to normal values after VUETIFY
  z-index: 1004;
}

@media screen and (max-width: $lg) {
  .sidebar {
    max-width: 400px;
  }
}
</style>
