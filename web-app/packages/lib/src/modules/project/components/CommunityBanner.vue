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
          :label="t('BrowseCommunityProjects')"
          @click.stop="click"
          data-cy="community-project-btn"
      /></template>
      <template #title>{{ t('CommunityProjects') }}</template>
      <template #description>{{
        t('ExploreVariousTemplateProjectsWithinOurCommunity')
      }}</template>
    </app-section-banner>
  </app-container>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'

import { ProjectRouteName } from '../routes'

import returnTranslation from '@/../../lang/translate'
import AppContainer from '@/common/components/AppContainer.vue'
import AppSectionBanner from '@/common/components/AppSectionBanner.vue'

const router = useRouter()
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

function click() {
  router.push({ name: ProjectRouteName.ProjectsExplore })
}
</script>
