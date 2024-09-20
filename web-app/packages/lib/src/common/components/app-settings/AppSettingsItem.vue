<template>
  <div
    :class="[
      'flex flex-column align-items-start',
      'row-gap-2',
      'md:align-items-center md:flex-row'
    ]"
  >
    <div class="flex-grow-1">
      <p class="title-t3">
        <slot name="title"></slot>
      </p>
      <span class="paragraph-p6 opacity-80">
        <slot name="description"></slot>
      </span>
    </div>
    <slot name="action"></slot>
  </div>
</template>

<script setup lang="ts">
// No props or additional logic needed
</script>
