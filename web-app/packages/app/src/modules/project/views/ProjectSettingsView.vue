<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-settings-view-template
    :namespace="namespace"
    :projectName="projectName"
    :show-settings="projectStore.isProjectOwner"
  >
  </project-settings-view-template>
</template>

<script setup lang="ts">
import { ProjectSettingsViewTemplate, useProjectStore } from '@mergin/lib'

defineProps<{ namespace: string; projectName: string }>()

const projectStore = useProjectStore()
</script>
