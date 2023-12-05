<template>
  <section class="surface-section p-4 border-round-3xl">
    <header
      v-if="!!$slots.title"
      class="flex justify-content-between align-items-center pb-4"
    >
      <h2 class="text-xl"><slot name="title"></slot></h2>
      <slot name="extra"></slot>
    </header>
    <slot></slot>
  </section>
</template>

<script lang="ts" setup></script>

<style scoped lang="scss"></style>
