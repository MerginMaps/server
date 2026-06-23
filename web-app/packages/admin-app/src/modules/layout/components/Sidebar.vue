<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: LicenseRef-MerginMaps-Commercial
-->

<script lang="ts">
export default {
  name: 'AdminSidebar'
}
</script>

<script setup lang="ts">
import { AdminRoutes, SidebarFooter } from '@mergin/admin-lib'
import { SideBarItemModel, SideBarTemplate } from '@mergin/lib'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import returnTranslation from '@/../../lang/translate'

const route = useRoute()
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const sidebarItems = computed<SideBarItemModel[]>(() => [
  {
    title: t('Overview'),
    to: '/overview',
    icon: 'ti ti-layout-dashboard',
    active: route.matched.some((item) => item.name === AdminRoutes.OVERVIEW)
  },
  {
    title: t('Accounts'),
    to: '/accounts',
    icon: 'ti ti-user-circle',
    active: route.matched.some((item) => item.name === AdminRoutes.ACCOUNTS)
  },
  {
    title: t('Projects'),
    to: '/projects',
    icon: 'ti ti-article',
    active: route.matched.some((item) => item.name === AdminRoutes.PROJECTS)
  },
  {
    title: t('Settings'),
    to: '/settings',
    icon: 'ti ti-settings',
    active: route.matched.some((item) => item.name === AdminRoutes.SETTINGS)
  }
])
</script>

<template>
  <side-bar-template :sidebarItems="sidebarItems">
    <template #subtitle>{{ t('AdminPanel') }}</template>
    <template #footer>
      <sidebar-footer />
    </template>
  </side-bar-template>
</template>

<style lang="scss" scoped></style>
