<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-row v-if="currentNamespace && accessRequests && accessRequestsCount > 0">
    <v-card class="bubble mt-3">
      <h3>Project access requests</h3>
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
      'accessRequests',
      'accessRequestsCount',
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
@use '@/sass/dashboard';
</style>
