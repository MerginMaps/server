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

import returnTranslation from '@/../../lang/translate'

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
    const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

    function openCloneDialog() {
      const dialogProps = {
        namespace: props.namespace,
        project: props.projectName
      }
      const dialog = {
        maxWidth: 580,
        persistent: true,
        header: t('CloneProject')
      }
      const listeners = {
        error: (error, data) => {
          formStore.handleError({
            componentId: data.merginComponentUuid,
            error,
            generalMessage: t('FailedToCloneProject')
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
        header: t('ShareProject')
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
