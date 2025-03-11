<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <clone-dialog-template
    v-bind="$props"
    :target-workspace="namespace"
    @on-clone-project="onCloneProject"
  />
</template>

<script lang="ts">
import { mapActions } from 'pinia'
import { defineComponent } from 'vue'

import CloneDialogTemplate from './CloneDialogTemplate.vue'

import { useProjectStore } from '@/modules/project/store'
import { CloneProjectParams } from '@/modules/project/types'

export default defineComponent({
  name: 'clone-dialog',
  props: {
    project: String,
    namespace: String
  },
  components: { CloneDialogTemplate },
  methods: {
    ...mapActions(useProjectStore, ['cloneProject']),

    async onCloneProject(
      project: string,
      namespace: string,
      data: CloneProjectParams,
      cbSuccess: () => void
    ) {
      try {
        await this.cloneProject({
          namespace,
          project,
          data,
          cbSuccess: async () => {
            cbSuccess()
            this.$emit('success', data)
          }
        })
      } catch (err) {
        this.$emit('error', err, data)
      }
    }
  }
})
</script>
