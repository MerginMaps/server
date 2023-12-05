<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-btn
    v-bind="$attrs"
    v-on="$listeners"
    :class="`${colorClass} white--text font-weight-bold ${
      // TODO: start to work in Vue 3 (remove this comment after upgrade to vue 3) - https://v3-migration.vuejs.org/breaking-changes/attrs-includes-class-style.html#attrs-includes-class-style
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
