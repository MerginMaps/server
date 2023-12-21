<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <aside>
    <PSidebar
      v-model:visible="model"
      :modal="true"
      position="right"
      class="w-11 lg:w-4"
    >
      <template #container="{ closeCallback }">
        <div class="flex flex-column h-full">
          <!-- Header -->
          <div
            class="flex align-items-center justify-content-between px-4 py-0"
          >
            <h4 class="flex-grow-1"><slot name="title"></slot></h4>
            <div class="flex-shrink-0">
              <slot name="headerButtons"></slot>
              <PButton
                type="button"
                @click="closeCallback"
                severity="secondary"
                icon="ti ti-x"
                text
                rounded
                class="p-1 text-2xl"
              ></PButton>
            </div>
          </div>

          <!-- content -->
          <div class="overflow-y-auto p-4 pt-6">
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
import { computed } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()
const emitModelValue = defineEmits(['update:modelValue'])
const model = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    return emitModelValue('update:modelValue', value)
  }
})
</script>

<style lang="scss" scoped></style>
