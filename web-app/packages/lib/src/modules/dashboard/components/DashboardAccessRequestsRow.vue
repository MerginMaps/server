<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container
    v-if="currentNamespace && accessRequests && accessRequestsCount > 0"
  >
    <app-section>
      <template #title
        >Requests
        <span class="text-color-medium-green"
          >({{ accessRequestsCount }})</span
        ></template
      >
      <template #default>
        <slot name="table" :namespace="currentNamespace"></slot>
      </template>
    </app-section>
  </app-container>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { AppContainer, AppSection } from '@/common/components'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'DashboardAccessRequestsRow',
  components: { AppSection, AppContainer },
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
