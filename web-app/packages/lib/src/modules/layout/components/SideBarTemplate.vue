<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <aside
    :class="[
      'sidebar',
      'fixed',
      'w-11',
      'h-screen',
      'top-0',
      'left-0',
      'overflow-auto',
      'surface-section',
      'transition-all',
      'transition-duration-500',
      'z-5',
      !isOpen ? '-translate-x-100' : 'xl:translate-x-0'
    ]"
  >
    <div class="flex flex-column justify-content-between h-screen">
      <div>
        <header class="p-2 xl:p-4 mb-2">
          <div class="xl:hidden flex justify-content-end">
            <PButton
              plain
              icon="ti ti-x"
              text
              rounded
              @click="onCloseClick"
              class="p-1 text-2xl"
            />
          </div>

          <div class="flex justify-content-center">
            <img src="@/assets/mm-logo.svg" />
          </div>

          <div
            v-if="$slots.subtitle"
            class="sidebar-subtitle w-full border-round-lg mt-4 p-2 text-center"
          >
            <p class="title-t3 text-color-forest">
              <slot name="subtitle"></slot>
            </p>
          </div>
        </header>

        <nav>
          <ul class="list-none p-0 m-0" data-cy="side-bar">
            <template v-for="item in initialSidebarItems" :key="item.to">
              <side-bar-item :item="item"></side-bar-item>
            </template>
            <slot name="items">
              <!-- sidebar items -->
            </slot>
          </ul>
        </nav>
      </div>
      <footer class="flex flex-column row-gap-3 p-3">
        <slot name="footer">
          <!-- footer content -->
          <template v-if="userStore.isSuperUser">
            <PDivider class="m-0" />
            <a
              href="/admin"
              target="__blank"
              class="flex justify-content-between align-items-center title-t5 no-underline cursor-pointer"
              >Admin Panel <i class="title-t1 ti ti-external-link"
            /></a>
          </template>
        </slot>
      </footer>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { SideBarItemModel } from '../types'

import { DashboardRouteName, useUserStore } from '@/main'
import SideBarItem from '@/modules/layout/components/SideBarItem.vue'
import { useLayoutStore } from '@/modules/layout/store'
import { ProjectRouteName } from '@/modules/project'

const route = useRoute()
const layoutStore = useLayoutStore()
const userStore = useUserStore()
const props = defineProps<{
  sidebarItems?: SideBarItemModel[]
}>()

const initialSidebarItems = computed<SideBarItemModel[]>(() => {
  return (
    props.sidebarItems || [
      {
        active: route.matched.some(
          (item) => item.name === DashboardRouteName.Dashboard
        ),
        title: 'Dashboard',
        to: '/dashboard',
        icon: 'ti ti-home'
      },
      {
        active: route.matched.some(
          (item) =>
            item.name === ProjectRouteName.Projects ||
            item.name === ProjectRouteName.Project
        ),
        title: 'Projects',
        to: '/projects',
        icon: 'ti ti-article'
      }
    ]
  )
})
const isOpen = computed<boolean>(() => layoutStore.drawer)

const onCloseClick = () => {
  layoutStore.setDrawer({ drawer: false })
}
</script>

<style lang="scss" scoped>
.sidebar {
  // Based on <main> grid values
  max-width: 16.66%;

  &-subtitle {
    background: rgb(183, 205, 196);
    background: linear-gradient(
      187deg,
      rgba(183, 205, 196, 1) 0%,
      rgba(223, 240, 232, 1) 85%,
      rgba(239, 245, 243, 1) 100%
    );
  }
}

@media screen and (max-width: $xl) {
  .sidebar {
    max-width: 400px;
  }
}
</style>
