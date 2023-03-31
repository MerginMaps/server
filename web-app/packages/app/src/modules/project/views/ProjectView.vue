<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-view-template
    :hide-namespace="true"
    :namespace="namespace"
    :projectName="projectName"
    :asAdmin="asAdmin"
    :location="location"
    :show-settings="isProjectOwner"
    :hide-clone-button="!canCreateProject"
    @open-clone-dialog="openCloneDialog"
  />
</template>

<script>
import { CloneDialog, ProjectViewTemplate } from '@mergin/lib'
import { computed } from '@vue/composition-api'
import { useActions, useGetters } from 'vuex-composition-helpers'

export default {
  name: 'ProjectView',
  components: {
    ProjectViewTemplate
  },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    },
    location: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const { show } = useActions('dialogModule', ['show'])
    const { isProjectOwner } = useGetters('projectModule', ['isProjectOwner'])
    const { isGlobalWorkspaceAdmin } = useGetters('userModule', [
      'isGlobalWorkspaceAdmin'
    ])
    const canCreateProject = computed(() => isGlobalWorkspaceAdmin?.value)

    function openCloneDialog() {
      const dialogProps = {
        namespace: props.namespace,
        project: props.projectName
      }
      const dialog = { maxWidth: 580, persistent: true }
      show({
        component: CloneDialog,
        params: {
          props: dialogProps,
          dialog
        }
      })
    }

    return {
      canCreateProject,
      isProjectOwner,
      openCloneDialog
    }
  }
}
</script>
