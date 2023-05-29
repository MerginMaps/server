<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-row>
    <v-col class="pa-0">
      <v-card class="mt-3" variant="outlined" color="white">
        <v-card-title><h3>Recent active projects</h3></v-card-title>
        <v-card-text style="padding-left: 0">
          <slot name="projects"></slot>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'DashboardProjectsRow'
})
</script>

<style scoped lang="scss">
</style>
