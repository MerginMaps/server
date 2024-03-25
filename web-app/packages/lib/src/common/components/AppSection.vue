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
    <header
      v-if="!!$slots.title || $slots.header"
      :class="[
        'flex',
        'flex-column',
        'lg:flex-row',
        'lg:align-items-center lg:justify-content-between',
        'row-gap-3',
        $slots.title ? 'p-4' : ''
      ]"
    >
      <h2 v-if="!!$slots.title" class="text-sm text-color">
        <slot name="title"></slot>
      </h2>
      <slot v-else-if="$slots.header" name="header"></slot>
      <div
        v-if="!!$slots.headerActions"
        class="flex align-items-center lg:justify-content-end"
      >
        <slot name="headerActions"></slot>
      </div>
    </header>
    <slot></slot>
  </section>
</template>

<script lang="ts" setup>
withDefaults(defineProps<{ ground?: boolean }>(), {
  ground: false
})
</script>

<style scoped lang="scss"></style>
