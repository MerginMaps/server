<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PDialog
    v-model:visible="dialogStore.isDialogOpen"
    modal
    :dismissableMask="!dialogProps.persistent"
    :close-on-escape="!dialogProps.persistent"
    :style="{
      maxWidth: `${dialogProps.maxWidth}px`
    }"
    :header="dialogProps.header ?? 'Action'"
    @close="close"
    :pt="{
      root: {
        class: 'w-10 lg:w-4 border-round-2xl'
      },
      header: {
        class: 'text-sm border-none border-round-top-2xl',
        style: {
          color: 'var(--forest-color)'
        }
      },
      closeButton: {
        style: {
          backgroundColor: 'var(--light-green-color)'
        }
      },
      content: {
        class: 'border-round-bottom-2xl'
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
