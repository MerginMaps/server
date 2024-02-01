<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <aside class="flex flex-column row-gap-4">
    <div class="flex flex-column row-gap-4">
      <div class="flex flex-column row-gap-1 p-input-filled">
        <slot name="accountsInput"></slot>
      </div>

      <div class="flex flex-column row-gap-1 p-input-filled">
        <label class="text-xs">Project permission</label>
        <app-dropdown :options="permissionStates" v-model="permission" />
      </div>
    </div>

    <slot></slot>

    <tip-message>
      <template #title> Mergin Maps permission system </template>
      <template #description>
        Learn more about permission system
        <a :href="docsUrl" target="_blank" class="text-color-forest">here</a>.
      </template>
    </tip-message>

    <!-- Footer -->
    <div
      class="flex flex-column lg:flex-row justify-content-between align-items-center py-4"
    >
      <PButton
        severity="secondary"
        @click.prevent="$emit('close')"
        class="flex w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6 justify-content-center"
        data-cy="clone-dialog-close-btn"
        >Cancel</PButton
      >

      <PButton
        id="share-project-btn"
        :disabled="disabled"
        @click.prevent="$emit('submit')"
        data-cy="project-form-create-btn"
        class="flex w-12 lg:w-6 justify-content-center"
      >
        Share
      </PButton>
    </div>
  </aside>
</template>

<script setup lang="ts" generic="T extends ">
import { computed } from 'vue'

import AppDropdown from '@/common/components/AppDropdown.vue'
import TipMessage from '@/common/components/TipMessage.vue'
import {
  ProjectRoleName,
  getProjectRoleNameValues
} from '@/common/permission_utils'
import { useInstanceStore } from '@/main'

const instanceStore = useInstanceStore()
const props = defineProps<{ modelValue: ProjectRoleName; disabled: boolean }>()
const emit = defineEmits<{
  'update:modelValue': [value: ProjectRoleName]
  close: []
  submit: []
}>()

const permissionStates = getProjectRoleNameValues()
const docsUrl = `${instanceStore.configData?.docs_url ?? ''}/manage/permissions`
// define proxyValue for modelValue to emit update:modelValue
const permission = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
})
</script>

<style scoped lang="scss"></style>
