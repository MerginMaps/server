<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <admin-projects-table :show-namespace="showNamespace" />
  </admin-layout>
</template>

<script setup lang="ts">
import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import AdminProjectsTable from '@/modules/admin/components/AdminProjectsTable.vue'

interface Props {
  showNamespace: boolean
}

withDefaults(defineProps<Props>(), {
  showNamespace: false
})
</script>

<style lang="scss" scoped></style>
