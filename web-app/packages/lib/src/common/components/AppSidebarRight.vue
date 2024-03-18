<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <aside>
    <PSidebar
      :auto-z-index="false"
      v-model:visible="model"
      :modal="true"
      position="right"
      class="w-11 lg:w-5 xl:w-3"
      :pt="{
        mask: {
          style: {
            // < then dialog zindex (7)
            zIndex: 6
          }
        }
      }"
    >
      <template #container="{ closeCallback }">
        <div class="flex flex-column h-full">
          <!-- Header -->
          <div
            class="flex align-items-center justify-content-between py-2 px-3"
          >
            <h4>
              <slot v-if="isScrollingContent" name="title"></slot>
            </h4>
            <div class="flex-shrink-0">
              <slot name="headerButtons"></slot>
              <PButton
                type="button"
                @click="closeCallback"
                icon="ti ti-x"
                plain
                text
                rounded
                class="p-1 text-2xl"
                data-cy="right-sidebar-close-btn"
              ></PButton>
            </div>
          </div>

          <!-- content -->
          <div class="overflow-y-auto p-4 pt-6" @scroll="scrollContent">
            <slot></slot>
          </div>

          <!-- foooter -->
          <div class="mt-auto w-full p-4">
            <slot name="footer"></slot>
          </div>
        </div>
      </template>
    </PSidebar>
  </aside>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()
const emitModelValue = defineEmits(['update:modelValue'])

const isScrollingContent = ref(false)

const model = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    return emitModelValue('update:modelValue', value)
  }
})

/**
 * Handles scrolling of sidebar content area.
 * Sets isScrollingContent ref to true if scroll position is past
 * first child element.
 */
function scrollContent(e) {
  const childRect = e.target.firstElementChild?.getBoundingClientRect()
  isScrollingContent.value = childRect?.y
    ? (e.currentTarget.scrollTop ?? 0) > childRect.y
    : !!e.currentTarget.scrollTop
}
</script>

<style lang="scss" scoped></style>
