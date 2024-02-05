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

    <!-- Footer -->
    <div
      class="flex flex-column lg:flex-row justify-content-between align-items-center py-4"
    >
      <a
        :href="docsUrl"
        target="_blank"
        class="text-color-forest w-12 lg:w-8 font-semibold"
        ><i class="ti ti-info-circle-filled mr-2" /><span class="underline"
          >Learn more about permission system</span
        ></a
      >.

      <PButton
        id="share-project-btn"
        :disabled="disabled"
        @click.prevent="$emit('submit')"
        data-cy="project-form-create-btn"
        class="flex w-12 lg:w-4 justify-content-center"
      >
        Share
      </PButton>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import AppDropdown from '@/common/components/AppDropdown.vue'
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
