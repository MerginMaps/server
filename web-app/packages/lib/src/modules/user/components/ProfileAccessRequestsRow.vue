<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card
    class="table"
    v-if="accessRequests && accessRequests.length > 0"
    variant="flat"
  >
    <v-card-text>
      <h3>Project access requests</h3>
      <project-access-request-table />
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import ProjectAccessRequestTable from '@/modules/project/components/ProjectAccessRequestTable.vue'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'ProfileAccessRequestsRow',
  components: { ProjectAccessRequestTable },
  computed: {
    ...mapState(useProjectStore, ['accessRequests'])
  },
  async created() {
    await this.initAccessRequests()
  },
  methods: {
    ...mapActions(useProjectStore, ['initAccessRequests'])
  }
})
</script>

<style scoped lang="scss"></style>
