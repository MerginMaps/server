<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-view-template
    :show-namespace="false"
    :namespace="namespace"
    :projectName="projectName"
    :show-settings="isProjectOwner"
    :hide-clone-button="!canCreateProject"
    @open-clone-dialog="openCloneDialog"
    @open-share-dialog="openShareDialog"
  />
</template>

<script lang="ts">
import {
  CloneDialog,
  ProjectShareDialog,
  ProjectViewTemplate,
  useDialogStore,
  useFormStore,
  useProjectStore,
  useUserStore
} from '@mergin/lib'
import { computed, defineComponent } from 'vue'

export default defineComponent({
  name: 'ProjectView',
  components: {
    ProjectViewTemplate
  },
  props: {
    namespace: String,
    projectName: String
  },
  setup(props) {
    const userStore = useUserStore()
    const projectStore = useProjectStore()
    const dialogStore = useDialogStore()
    const formStore = useFormStore()

    const canCreateProject = computed(() => userStore.isGlobalWorkspaceAdmin)
    const isProjectOwner = computed(() => projectStore.isProjectOwner)

    function openCloneDialog() {
      const dialogProps = {
        namespace: props.namespace,
        project: props.projectName
      }
      const dialog = {
        maxWidth: 580,
        persistent: true,
        header: 'Clone project'
      }
      const listeners = {
        error: (error, data) => {
          formStore.handleError({
            componentId: data.merginComponentUuid,
            error,
            generalMessage: 'Failed to clone project'
          })
        }
      }
      dialogStore.show({
        component: CloneDialog,
        params: {
          props: dialogProps,
          listeners,
          dialog
        }
      })
    }

    function openShareDialog() {
      const dialog = {
        maxWidth: 600,
        header: 'Share project'
      }
      dialogStore.show({
        component: ProjectShareDialog,
        params: {
          dialog
        }
      })
    }

    return {
      canCreateProject,
      isProjectOwner,
      openCloneDialog,
      openShareDialog
    }
  }
})
</script>
