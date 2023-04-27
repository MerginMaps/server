<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-settings-view-template
    :namespace="namespace"
    :projectName="projectName"
    :asAdmin="asAdmin"
    :show-settings="isProjectOwner"
  >
    <!-- TODO: V3_UPGRADE [MERGIN-EXT] - change settingsAccess to settings.access  -->
    <template #permissions="{ settings, keyProp, saveProject }">
      <project-permissions-template
        v-model="settings.access"
        :key="keyProp"
        @save-project="saveProject(...arguments)"
      />
    </template>
  </project-settings-view-template>
</template>

<script lang="ts">
import {
  ProjectSettingsViewTemplate,
  ProjectPermissionsTemplate
} from '@mergin/lib'
import { defineComponent } from 'vue'
import { useGetters } from 'vuex-composition-helpers'

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
    const { isProjectOwner } = useGetters('projectModule', ['isProjectOwner'])

    return {
      isProjectOwner
    }
  }
})
</script>
