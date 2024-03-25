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
        class: 'border-transparent w-full border-round-xl',
        onclick: (e) => {
          // if in clickable area, there is problem with bubbling
          e.stopPropagation()
        }
      },
      input: {
        class: 'text-xs border-round-xl'
      },
      item({ context }) {
        return {
          class: [
            'text-color p-2 hover:bg-gray-100 bg-transparent',
            context.focused ? 'bg-gray-50' : 'bg-transparent'
          ]
        }
      },
      trigger(options) {
        return {
          class: options.props?.disabled ? 'text-color' : 'text-color-forest'
        }
      },
      panel: {
        style: {
          zIndex: 2101
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
          'font-semibold text-base'
        ]"
      ></i>
    </template>
    <template #option="{ option }">
      <div class="flex text-xs align-items-center py-2">
        <div class="flex flex-column mr-6 gap-2">
          <p
            :class="[
              option.description && 'font-semibold',
              'overflow-wrap-anywhere'
            ]"
          >
            {{ option.label }}
          </p>
          <span v-if="option.description" class="overflow-wrap-anywhere">{{
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
    if (
      props.options.find(
        (item) => item.disabled === true && item.value === value
      )
    ) {
      return
    }
    return emitModelValue('update:modelValue', value)
  }
})

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<style scoped lang="scss"></style>
