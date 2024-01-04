<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PDropdown
    :options="options"
    option-label="label"
    option-value="value"
    v-model="model"
    @show="toggle"
    @hide="toggle"
    :pt="{
      root: {
        class: 'border-transparent w-full bg-transparent',
        onclick: (e) => {
          // if in clickable area, there is problem with bubbling
          e.stopPropagation()
        }
      },
      input: {
        class: 'text-xs'
      },
      item({ context }) {
        return {
          class: [
            'text-color p-2 hover:bg-gray-100',
            context.focused ? 'bg-gray-50' : 'bg-transparent'
          ]
        }
      }
    }"
  >
    <template #dropdownicon="scope">
      <i
        :class="[
          scope.class,
          'ti',
          isOpen ? 'ti-chevron-up' : 'ti-chevron-down',
          'text-color-forest font-semibold text-xl'
        ]"
      ></i>
    </template>
    <template #option="{ option }">
      <div class="flex text-xs align-items-center py-2">
        <div class="flex flex-column mr-6">
          <p class="font-semibold m-0">{{ option.label }}</p>
          <span v-if="option.description" class="pt-2">{{
            option.description
          }}</span>
        </div>
        <div class="ml-auto px-2">
          <i
            :class="[
              'ti ti-circle-check-filled text-color-forest',
              modelValue === option.value ? 'visible' : 'hidden'
            ]"
          ></i>
        </div>
      </div>
    </template>
  </PDropdown>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'

import { DropdownOption } from './types'

const props = defineProps<{
  modelValue: string
  options: DropdownOption[]
}>()
const isOpen = ref(false)

const emitModelValue = defineEmits(['update:modelValue'])
const model = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    return emitModelValue('update:modelValue', value)
  }
})

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<style scoped lang="scss"></style>