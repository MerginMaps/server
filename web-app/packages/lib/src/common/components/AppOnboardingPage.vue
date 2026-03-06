<template>
  <article :class="['relative', 'grid grid-nogutter', 'h-full']">
    <!-- Logo -->
    <aside
      :class="[
        'fixed top-0 left-0 p-3 md:p-4 z-1 w-full md:w-auto surface-ground',
        { 'onborading-page-logo': $slots.aside }
      ]"
    >
      <template v-if="brandingLogoUrl && !customLogoLoadFailed">
        <img
          class="logo-image"
          :src="brandingLogoUrl"
          @error="onCustomLogoError"
          alt="Not Found"
        />
      </template>
      <slot v-else name="logo">
        <img class="logo-image" :src="defaultLogoUrl" alt="Not Found" />
      </slot>
    </aside>

    <!-- Side content if defined is displayed on tablets > -->
    <aside
      v-if="$slots.aside"
      :class="[
        'hidden md:block md:col-3',
        'fixed top-0 left-0 bottom-0 z-0 h-full'
      ]"
    >
      <slot name="aside"></slot>
    </aside>

    <!-- Content section -->
    <div
      :class="[
        'flex flex-column row-gap-4 align-items-center justify-content-center',
        'p-4 lg:p-0',
        $slots.aside ? 'col-12 md:col-9 md:col-offset-3' : 'col-12'
      ]"
    >
      <section
        class="flex flex-column gap-4 w-full"
        :style="{ maxWidth: contentMaxWidth }"
      >
        <header class="align-self-center text-center mt-5 md:mt-0">
          <slot name="header"></slot>
        </header>
        <slot></slot>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useInstanceStore } from '@/modules/instance/store'
import defaultLogoUrl from '@/assets/mm-logo.svg'

const customLogoLoadFailed = ref(false)
function onCustomLogoError(): void {
  customLogoLoadFailed.value = true
}
const instanceStore = useInstanceStore()
const brandingLogoUrl = computed(
  () => instanceStore.configData?.['dashboard_logo_url'] as string
)

withDefaults(defineProps<{ contentMaxWidth?: string }>(), {
  contentMaxWidth: '480px'
})
</script>

<style scoped lang="scss">
.logo-image {
  display: block;
  width: auto;
  height: 24px;
  max-width: 129px;
  max-height: 24px;
  object-fit: contain;
}

@media screen and (min-width: $md) {
  .onborading-page-logo {
    // reset background on tablet > screens
    background-color: transparent !important;
  }
}
</style>
