<template>
  <section class="surface-section border-round-2xl overflow-hidden">
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

<script lang="ts" setup></script>

<style scoped lang="scss"></style>
