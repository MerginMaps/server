<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PDialog
    :auto-z-index="false"
    v-model:visible="dialogStore.isDialogOpen"
    modal
    :dismissableMask="!dialogProps.persistent"
    :close-on-escape="!dialogProps.persistent"
    :header="dialogProps.header ?? 'Action'"
    :draggable="false"
    @close="close"
    :pt="{
      root: {
        style: {
          maxWidth: `${dialogProps.maxWidth}px`
        },
        class: 'w-10 md:w-8 lg:w-6 xl:w-4 max-w-30rem border-round-2xl'
      }
    }"
  >
    <component
      v-if="params"
      :is="component"
      v-bind="params.props"
      v-on="dialogListeners"
    />
  </PDialog>
</template>

<script lang="ts">
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules/dialog/store'

export default defineComponent({
  setup() {
    const dialogStore = useDialogStore()
    return { dialogStore }
  },
  computed: {
    ...mapState(useDialogStore, ['params', 'component', 'dialogProps']),

    dialogListeners() {
      return this.params?.listeners ?? {}
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['close'])
  }
})
</script>

<style scoped lang="scss"></style>
