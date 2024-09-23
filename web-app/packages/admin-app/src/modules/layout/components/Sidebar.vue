<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: LicenseRef-MerginMaps-Commercial
-->

<script setup lang="ts">
import { AdminRoutes } from '@mergin/admin-lib'
import { SideBarItemModel, SideBarTemplate } from '@mergin/lib'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const sidebarItems = computed<SideBarItemModel[]>(() => [
  {
    title: 'Accounts',
    to: '/accounts',
    icon: 'ti ti-user-circle',
    active: route.matched.some((item) => item.name === AdminRoutes.ACCOUNTS)
  },
  {
    title: 'Projects',
    to: '/projects',
    icon: 'ti ti-article',
    active: route.matched.some((item) => item.name === AdminRoutes.PROJECTS)
  },
  {
    title: 'Settings',
    to: '/settings',
    icon: 'ti ti-settings',
    active: route.matched.some((item) => item.name === AdminRoutes.SETTINGS)
  }
])
</script>

<template>
  <side-bar-template :sidebarItems="sidebarItems" />
</template>

<style lang="scss" scoped></style>
