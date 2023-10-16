<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <projects-view-template :namespace="namespace" />
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import ProjectsViewTemplate from '@/modules/admin/components/ProjectsViewTemplate.vue'

export default defineComponent({
  name: 'ProjectsView',
  components: {
    ProjectsViewTemplate
  },
  props: {
    namespace: String
  }
})
</script>

<style lang="scss" scoped></style>
