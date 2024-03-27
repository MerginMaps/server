<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-collaborators-view-template
    v-if="isProjectOwner"
    @share="openShareDialog"
    :allow-share="!instanceStore.globalRolesEnabled"
    :show-access-requests="userStore.isGlobalWorkspaceAdmin"
  />
</template>

<script setup lang="ts">
import {
  ProjectShareDialog,
  ProjectCollaboratorsViewTemplate,
  useDialogStore,
  useProjectStore,
  useUserStore,
  useInstanceStore,
  useNotificationStore
} from '@mergin/lib'
import { getErrorMessage } from '@mergin/lib/types/common/error_utils';
import { computed } from 'vue'

const projectStore = useProjectStore()
const dialogStore = useDialogStore()
const userStore = useUserStore()
const instanceStore = useInstanceStore()
const notificationStore = useNotificationStore()

const isProjectOwner = computed(() => projectStore.isProjectOwner)

function openShareDialog() {
  const dialog = {
    maxWidth: 600,
    header: `Share project ${projectStore.project?.name}`
  }
  dialogStore.show({
    component: ProjectShareDialog,
    params: {
      dialog,
      listeners: {
        onShareError: (err) => {
          notificationStore.error({
            text: getErrorMessage(err, 'Failed to save project settings')
          })
        }
      }
    }
  })
}
</script>
