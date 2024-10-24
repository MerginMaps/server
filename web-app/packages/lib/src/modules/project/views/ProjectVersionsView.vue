<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-versions-view-template
    :projectName="projectName"
    :namespace="namespace"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import ProjectVersionsViewTemplate from '@/modules/project/views/ProjectVersionsViewTemplate.vue'

export default defineComponent({
  name: 'ProjectVersionsView',
  components: { ProjectVersionsViewTemplate },
  props: {
    projectName: String,
    namespace: String
  }
})
</script>

<style lang="scss" scoped></style>
