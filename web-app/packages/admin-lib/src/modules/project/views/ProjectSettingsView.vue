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
    :show-access-requests="true"
  >
  </project-settings-view-template>
</template>

<script lang="ts">
import { ProjectSettingsViewTemplate } from '@mergin/lib'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ProjectSettingsView',
  components: {
    ProjectSettingsViewTemplate
  },
  props: {
    namespace: String,
    projectName: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  }
})
</script>
