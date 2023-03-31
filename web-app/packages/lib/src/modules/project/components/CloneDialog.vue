<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <clone-dialog-template v-bind="$props" @on-clone-project="onCloneProject" />
</template>

<script lang="ts">
import { AxiosError } from 'axios'
import Vue from 'vue'
import { mapActions } from 'vuex'

import CloneDialogTemplate from './CloneDialogTemplate.vue'
import { CloneProjectParams } from '@/modules/project/types'

export default Vue.extend({
  name: 'clone-dialog',
  props: {
    project: String,
    namespace: String
  },
  components: { CloneDialogTemplate },
  methods: {
    ...mapActions('projectModule', ['cloneProject']),

    async onCloneProject(
      project: string,
      namespace: string,
      data: CloneProjectParams,
      cbSuccess: () => void,
      cbError: (err: AxiosError) => void
    ) {
      await this.cloneProject({
        namespace,
        project,
        data,
        cbSuccess,
        cbError
      })
    }
  }
})
</script>
