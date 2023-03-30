<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card class="mt-6 pa-4">
    <div class="flex-row justify-space-between" style="display: flex">
      <div class="flex-column" style="max-width: 70%">
        <h3 class="black--text">Anonymous data collection</h3>
        <div>
          Mergin Maps collects anonymous usage information to make the service
          better overtime. You can opt-out anytime.
          <a class="black--text" :href="docsLinkMerginCe" target="_blank">
            Click here to learn more.
          </a>
        </div>
      </div>
      <v-switch
        color="secondary"
        v-model="usageStatus"
        disabled
        hide-details
        inset
      ></v-switch>
    </div>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapState } from 'vuex'

export default Vue.extend({
  name: 'UsageInformationCard',
  computed: {
    ...mapState('instanceModule', ['configData']),
    usageStatus() {
      return this.configData?.collect_statistics
    },
    docsLinkMerginCe(): string {
      return `${this.configData?.docs_url ?? ''}/dev/mergince/`
    }
  }
})
</script>

<style scoped></style>
