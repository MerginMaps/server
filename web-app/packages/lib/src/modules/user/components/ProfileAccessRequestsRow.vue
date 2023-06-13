<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card class="table" v-if="accessRequests && accessRequestsCount > 0" flat>
    <v-card-text>
      <h3>Project access requests</h3>
      <project-access-request-table />
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions, mapState } from 'vuex'

import ProjectAccessRequestTable from '@/modules/project/components/ProjectAccessRequestTable.vue'

export default Vue.extend({
  name: 'ProfileAccessRequestsRow',
  components: { ProjectAccessRequestTable },
  computed: {
    ...mapState('projectModule', ['accessRequests', 'accessRequestsCount'])
  },
  async created() {
    await this.initUserAccessRequests()
  },
  methods: {
    ...mapActions('projectModule', ['initUserAccessRequests'])
  }
})
</script>

<style scoped lang="scss"></style>
