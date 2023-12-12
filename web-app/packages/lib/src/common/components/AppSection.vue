<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section
    :class="[
      ground
        ? 'surface-ground'
        : 'surface-section border-round-2xl overflow-hidden'
    ]"
  >
    <header
      v-if="!!$slots.title"
      class="flex justify-content-between align-items-center p-4"
    >
      <h2 class="text-sm text-color"><slot name="title"></slot></h2>
      <slot name="extra"></slot>
    </header>
    <slot></slot>
  </section>
</template>

<script lang="ts" setup>
withDefaults(defineProps<{ ground: boolean }>(), {
  ground: false
})
</script>

<style scoped lang="scss"></style>
