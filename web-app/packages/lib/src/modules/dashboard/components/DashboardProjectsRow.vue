<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!-- Projects -->
  <app-container>
    <app-section>
      <template #title>Recent active projects</template>
      <projects-table-data-loader
        :show-namespace="false"
        :showFooter="false"
        :public="false"
        :can-create-project="canCreateProject"
        :initialOptions="initialOptions"
      />
    </app-section>
  </app-container>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

import { AppContainer, AppSection } from '@/common'
import ProjectsTableDataLoader from '@/modules/project/components/ProjectsTableDataLoader.vue'
defineProps<{ canCreateProject: boolean }>()

const initialOptions = reactive({
  sortBy: 'updated',
  sortDesc: true,
  itemsPerPage: 5,
  page: 1
})
</script>
