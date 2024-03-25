<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card class="table" v-if="accessRequests && accessRequestsCount > 0" flat>
    <v-card-text>
      <h3>You requested access to these projects</h3>
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
    ...mapState(useProjectStore, ['accessRequests', 'accessRequestsCount'])
  },
  async created() {
    await this.initUserAccessRequests()
  },
  methods: {
    ...mapActions(useProjectStore, ['initUserAccessRequests'])
  }
})
</script>

<style scoped lang="scss"></style>
