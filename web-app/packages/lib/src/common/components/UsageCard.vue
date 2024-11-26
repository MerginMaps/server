<template>
  <div>
    <div
      :class="[
        'flex flex-column align-items-start row-gap-1',
        'p-4 border-round-lg',
        'surface-card',
        'h-full w-full'
      ]"
    >
      <h3 v-if="$slots.heading" class="title-t3 text-color mb-2">
        <slot name="heading" />
      </h3>

      <slot />

      <h4 class="headline-h2 overflow-wrap-anywhere">
        <slot name="title"></slot>
      </h4>

      <p class="paragraph-p4 opacity-60">
        <slot name="subtitle" />
      </p>

      <div class="mt-auto w-full">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
</script>

<style scoped lang="scss"></style>
