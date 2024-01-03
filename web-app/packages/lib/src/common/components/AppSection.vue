<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <section
    :class="[
      ground
        ? 'surface-ground'
        : 'surface-section border-round-xl overflow-hidden'
    ]"
  >
    <header v-if="!!$slots.title" class="flex align-items-center p-4">
      <h2 class="text-sm text-color"><slot name="title"></slot></h2>
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
