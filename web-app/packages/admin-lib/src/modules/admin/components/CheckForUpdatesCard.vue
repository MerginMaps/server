<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card class="mt-6 pa-4">
    <div class="flex-row justify-space-between" style="display: flex">
      <div class="flex-column" style="max-width: 70%">
        <h3 class="black--text">Check for updates</h3>
        <div>
          Let Mergin Maps automatically check for new updates to ensure you can
          always use the latest features
        </div>
      </div>
      <v-switch
        color="secondary"
        v-model="checkUpdates"
        hide-details
        inset
        @change="onChangeSwitch"
      ></v-switch>
    </div>
  </v-card>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useAdminStore } from '@/modules/admin/store'

export default defineComponent({
  name: 'CheckForUpdatesCard',
  computed: {
    ...mapState(useAdminStore, ['checkForUpdates'])
  },
  data() {
    return {
      checkUpdates: true
    }
  },
  watch: {
    checkForUpdates: {
      immediate: true,
      async handler(value) {
        this.checkUpdates = value === undefined ? true : value
      }
    }
  },
  methods: {
    ...mapActions(useAdminStore, ['setCheckUpdatesToCookies']),
    onChangeSwitch(value) {
      this.setCheckUpdatesToCookies({ value })
    }
  }
})
</script>

<style scoped></style>
