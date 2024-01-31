<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section-banner>
      <template #header-image>
        <img width="50" height="50" src="@/assets/globe.svg" />
      </template>
      <template #header-actions
        ><PButton
          label="Browse community projects"
          @click.stop="click"
          data-cy="community-project-btn"
      /></template>
      <template #title>Community projects</template>
      <template #description
        >Explore various template projects within our community.</template
      >
    </app-section-banner>
  </app-container>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'

import { ProjectRouteName } from '../routes'

import AppContainer from '@/common/components/AppContainer.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'

const router = useRouter()

function click() {
  router.push({ name: ProjectRouteName.ProjectsExplore })
}
</script>
