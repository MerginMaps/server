<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-btn
    v-bind="$attrs"
    :class="`${colorClass} white--text font-weight-bold ${
      $attrs.class ? $attrs.class : ''
    }`"
  >
    <span class="mr-2 d-inline-flex">
      <slot name="icon" />
    </span>
    <span>
      <slot />
    </span>
  </v-btn>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ActionButton',
  props: {
    colorClass: { type: String, default: 'primary' }
  }
})
</script>

<style scoped></style>
