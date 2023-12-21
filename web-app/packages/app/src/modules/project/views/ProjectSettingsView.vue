<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  Hopaa
  <!-- <project-settings-view-template
    :namespace="namespace"
    :projectName="projectName"
    :asAdmin="asAdmin"
    :show-settings="projectStore.isProjectOwner"
    :show-access-requests="userStore.isGlobalWorkspaceAdmin"
  >
    <template #permissions="{ settings, keyProp, saveProject }">
      <project-permissions-template
        v-model="settings.access"
        :key="keyProp"
        @save-project="saveProject(...arguments)"
      />
    </template>
  </project-settings-view-template> -->
</template>

<script lang="ts">
import {
  ProjectSettingsViewTemplate,
  ProjectPermissionsTemplate,
  useProjectStore,
  useUserStore
} from '@mergin/lib'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ProjectSettingsView',
  components: {
    ProjectSettingsViewTemplate,
    ProjectPermissionsTemplate
  },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  setup(_props) {
    const projectStore = useProjectStore()
    const userStore = useUserStore()

    return {
      projectStore,
      userStore
    }
  }
})
</script>
