<template>
  <article :class="['relative', 'grid grid-nogutter', 'h-full']">
    <!-- Logo -->
    <aside class="absolute top-0 left-0 m-4">
      <slot name="logo">
        <img src="@/assets/mm-logo.svg" />
      </slot>
    </aside>

    <!-- Side content if defined -->
    <aside v-if="$slots.aside" class="col-3">
      <slot name="aside"></slot>
    </aside>

    <!-- Content section -->
    <div
      :class="[
        'flex flex-column row-gap-4 align-items-center justify-content-center',
        'p-4 lg:p-0',
        $slots.aside ? 'col-9' : 'col-12'
      ]"
    >
      <header class="align-self-center text-center">
        <slot name="header"></slot>
      </header>

      <section
        class="flex flex-column gap-4 w-full"
        :style="{ maxWidth: contentMaxWidth }"
      >
        <slot></slot>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ contentMaxWidth?: string }>(), {
  contentMaxWidth: '480px'
})
</script>

<style scoped lang="scss"></style>
