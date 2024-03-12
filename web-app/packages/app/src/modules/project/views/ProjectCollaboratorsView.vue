<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-collaborators-view-template
    v-if="isProjectOwner"
    @share="openShareDialog"
    :show-access-requests="userStore.isGlobalWorkspaceAdmin"
  />
</template>

<script setup lang="ts">
import {
  ProjectShareDialog,
  ProjectCollaboratorsViewTemplate,
  useDialogStore,
  useProjectStore,
  useUserStore
} from '@mergin/lib'
import { computed } from 'vue'

const projectStore = useProjectStore()
const dialogStore = useDialogStore()
const userStore = useUserStore()

const isProjectOwner = computed(() => projectStore.isProjectOwner)

function openShareDialog() {
  const dialog = {
    maxWidth: 600,
    header: `Share project ${projectStore.project?.name}`
  }
  dialogStore.show({
    component: ProjectShareDialog,
    params: {
      dialog
    }
  })
}
</script>
