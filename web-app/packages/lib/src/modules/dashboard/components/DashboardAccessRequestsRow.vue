<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-section
    v-if="currentNamespace && accessRequests && accessRequests.length > 0"
  >
    <template #title>Project access requests</template>
    <template #default>
      <slot name="table" :namespace="currentNamespace"></slot>
    </template>
  </app-section>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { AppSection } from '@/common/components'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'DashboardAccessRequestsRow',
  components: { AppSection },
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
            namespace: value,
            params: null
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
