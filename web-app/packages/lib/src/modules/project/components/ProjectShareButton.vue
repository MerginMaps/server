<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-share-button-template v-if="canShareProject" />
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { mapGetters, mapState } from 'vuex'

import ProjectShareButtonTemplate from './ProjectShareButtonTemplate.vue'

export default defineComponent({
  components: { ProjectShareButtonTemplate },
  computed: {
    ...mapGetters('userModule', ['currentWorkspace']),
    ...mapState('projectModule', ['project']),
    ...mapGetters('projectModule', ['isProjectOwner']),

    canShareProject() {
      return (
        this.project?.workspace_id === this.currentWorkspace?.id &&
        this.isProjectOwner
      )
    }
  }
})
</script>

<style lang="scss" scoped></style>
