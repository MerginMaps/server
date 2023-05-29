<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-row
    v-if="
      currentNamespace &&
      namespaceAccessRequests &&
      namespaceAccessRequests.length > 0
    "
  >
    <v-card variant="tonal" class="mt-3">
      <v-card-title><h3>Project access requests</h3></v-card-title>
      <v-card-text>
        <slot name="table" :namespace="currentNamespace"></slot>
      </v-card-text>
    </v-card>
  </v-row>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'DashboardAccessRequestsRow',
  computed: {
    ...mapState(useProjectStore, [
      'namespaceAccessRequests',
      'currentNamespace'
    ])
  },
  watch: {
    currentNamespace: {
      immediate: true,
      async handler(value) {
        if (value) {
          await this.initNamespaceAccessRequests({
            namespace: value
          })
        }
      }
    }
  },
  methods: {
    ...mapActions(useProjectStore, ['initNamespaceAccessRequests'])
  }
})
</script>

<style scoped lang="scss">
</style>
