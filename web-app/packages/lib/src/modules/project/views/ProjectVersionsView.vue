<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-versions-view-template
    :projectName="projectName"
    :namespace="namespace"
    :asAdmin="asAdmin"
  />
</template>

<script lang="ts">
import Vue from 'vue'

import MerginAPIMixin from '@/common/mixins/MerginAPIMixin'
import ProjectVersionsViewTemplate from '@/modules/project/views/ProjectVersionsViewTemplate.vue'

export default Vue.extend({
  name: 'ProjectVersionsView',
  components: { ProjectVersionsViewTemplate },
  mixins: [MerginAPIMixin],
  props: {
    projectName: String,
    namespace: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  }
})
</script>

<style lang="scss" scoped></style>
