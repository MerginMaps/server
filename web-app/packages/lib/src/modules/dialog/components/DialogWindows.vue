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
    <div
      v-if="params"
      :is="params.component"
      v-bind="params.props"
      v-on="params.listeners"
    />
  </v-dialog>
</template>

<script lang="ts">
import { mapState, mapGetters, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules/dialog/store'

export default defineComponent({
  computed: {
    ...mapState(useDialogStore, ['isDialogOpen', 'params']),
    ...mapGetters(useDialogStore, ['dialogProps'])
  },
  methods: {
    ...mapActions(useDialogStore, ['close'])
  }
})
</script>
