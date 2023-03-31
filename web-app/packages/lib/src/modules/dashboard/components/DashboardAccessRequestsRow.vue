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
    <v-card class="bubble mt-3">
      <h3>Project access requests</h3>
      <v-card-text>
        <project-access-request-table :namespace="currentNamespace" />
      </v-card-text>
    </v-card>
  </v-row>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions, mapState } from 'vuex'

import ProjectAccessRequestTable from '@/modules/project/components/ProjectAccessRequestTable.vue'

export default Vue.extend({
  name: 'DashboardAccessRequestsRow',
  components: { ProjectAccessRequestTable },
  computed: {
    ...mapState('projectModule', [
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
    ...mapActions('projectModule', ['initNamespaceAccessRequests'])
  }
})
</script>

<style scoped lang="scss">
@import 'src/sass/dashboard';
</style>
