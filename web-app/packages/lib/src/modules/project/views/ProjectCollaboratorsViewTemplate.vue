<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <!-- Searching -->
    <app-container>
      <app-section ground>
        <div class="flex align-items-center gap-2">
          <span class="p-input-icon-left flex-grow-1">
            <i class="ti ti-search text-xl"></i>
            <PInputText
              placeholder="Search members"
              data-cy="search-members-field"
              v-model="projectStore.accessSearch"
              class="w-full"
            />
          </span>
          <PButton
            @click="$emit('share')"
            icon="ti ti-send"
            label="Share"
            data-cy="project-share-btn"
          />
          <AppMenu :items="filterMenuItems" />
        </div>
      </app-section>
    </app-container>
    <slot>
      <project-members-table></project-members-table>
    </slot>

    <app-container v-if="$slots.banner"><slot name="banner" /></app-container>
  </div>
</template>

<script setup lang="ts">
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { computed } from 'vue'

import { ProjectMembersTable } from '../components'
import { useProjectStore } from '../store'

import AppContainer from '@/common/components/AppContainer.vue'
import AppMenu from '@/common/components/AppMenu.vue'
import AppSection from '@/common/components/AppSection.vue'

defineEmits<{ share: [] }>()

const projectStore = useProjectStore()
const filterMenuItems = computed<MenuItem[]>(() =>
  [
    {
      label: 'Sort by name A-Z',
      key: 'username',
      value: 'username',
      sortDesc: false
    },
    {
      label: 'Sort by name Z-A',
      key: 'name-desc',
      value: 'username',
      sortDesc: true
    }
  ].map((item) => ({
    ...item,
    command: (e: MenuItemCommandEvent) => {
      projectStore.accessSorting = {
        sortBy: e.item.value,
        sortDesc: e.item.sortDesc
      }
    },
    class:
      projectStore.accessSorting?.sortBy === item.value &&
      projectStore.accessSorting?.sortDesc === item.sortDesc
        ? 'bg-primary-400'
        : ''
  }))
)
</script>

<style lang="scss" scoped></style>
