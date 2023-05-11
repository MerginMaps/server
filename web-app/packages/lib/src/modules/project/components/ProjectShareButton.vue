<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-share-button-template v-if="canShareProject" />
</template>

<script lang="ts">
import { mapGetters, mapState } from 'pinia'
import { defineComponent } from 'vue'

import ProjectShareButtonTemplate from './ProjectShareButtonTemplate.vue'

import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  components: { ProjectShareButtonTemplate },
  computed: {
    ...mapGetters(useUserStore, ['currentWorkspace']),
    ...mapState(useProjectStore, ['project']),
    ...mapGetters(useProjectStore, ['isProjectOwner']),

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
