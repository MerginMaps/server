<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-settings-view-template
    :namespace="namespace"
    :projectName="projectName"
    :asAdmin="asAdmin"
    :show-settings="true"
  >
    <template #permissions="{ settingsAccess, keyProp, saveProject }">
      <project-permissions-template
        v-model="settingsAccess"
        :key="keyProp"
        @save-project="saveProject(...arguments)"
      />
    </template>
  </project-settings-view-template>
</template>

<script>
import {
  ProjectSettingsViewTemplate,
  ProjectPermissionsTemplate
} from '@mergin/lib'

export default {
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
  }
}
</script>
