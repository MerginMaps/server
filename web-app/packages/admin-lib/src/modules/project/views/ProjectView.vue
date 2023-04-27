<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <project-view-template
      :namespace="namespace"
      :projectName="projectName"
      :asAdmin="asAdmin"
      :location="location"
      :show-settings="true"
      @open-clone-dialog="openCloneDialog"
    />
  </admin-layout>
</template>

<script lang="ts">
import { CloneDialog, ProjectViewTemplate } from '@mergin/lib'
import { defineComponent } from 'vue'
import { useActions } from 'vuex-composition-helpers'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

export default defineComponent({
  name: 'ProjectView',
  components: {
    AdminLayout,
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
    const { handleError } = useActions('formModule', ['handleError'])

    function openCloneDialog() {
      const dialogProps = {
        namespace: props.namespace,
        project: props.projectName
      }
      const dialog = { maxWidth: 580, persistent: true }
      const listeners = {
        error: (error, data) => {
          handleError({
            componentId: data.merginComponentUuid,
            error,
            generalMessage: 'Failed to clone project'
          })
        }
      }
      show({
        component: CloneDialog,
        params: {
          props: dialogProps,
          listeners,
          dialog
        }
      })
    }

    return {
      openCloneDialog
    }
  }
})
</script>
