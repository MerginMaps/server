<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card
    class="bubble mt-3"
    style="background-color: #ffc863; color: rgba(0, 0, 0, 0.87); padding: 10px"
    outlined
  >
    <slot name="message"></slot>
  </v-card>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'WarningMessageTemplate'
})
</script>

<style scoped></style>
