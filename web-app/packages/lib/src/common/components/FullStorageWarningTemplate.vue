<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card
    class="bubble mt-3"
    style="background-color: #fce8e6; color: rgba(0, 0, 0, 0.87)"
    outlined
  >
    <span>
      <b>Your storage is almost full ({{ usage }}%).</b> Soon you will not be
      able to sync your projects.
      <slot name="buttons"></slot>
    </span>
  </v-card>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'FullStorageWarningTemplate',
  props: {
    usage: Number
  }
})
</script>

<style scoped></style>
