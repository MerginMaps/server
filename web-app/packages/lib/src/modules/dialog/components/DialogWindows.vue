<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-dialog
    :model-value="isDialogOpen"
    v-bind="dialogProps"
    @update:model-value="close"
  >
    <component
      v-if="params"
      :is="component"
      v-bind="params.props"
      v-on="dialogListeners"
    />
  </v-dialog>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules/dialog/store'

export default defineComponent({
  computed: {
    ...mapState(useDialogStore, [
      'isDialogOpen',
      'params',
      'component',
      'dialogProps'
    ]),

    dialogListeners() {
      return this.params?.listeners ?? {}
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['close'])
  }
})
</script>
