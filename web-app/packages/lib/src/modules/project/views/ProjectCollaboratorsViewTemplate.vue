<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container
      v-if="showAccessRequests && projectStore.accessRequestsCount > 0"
    >
      <app-section
        ><template #title
          >Requests
          <span class="opacity-80"
            >({{ projectStore.accessRequestsCount }})</span
          ></template
        ><project-access-requests
      /></app-section>
    </app-container>
    <!-- Searching -->
    <app-container>
      <app-section ground>
        <div class="flex align-items-center gap-2">
          <span class="p-input-icon-left flex-grow-1">
            <i class="ti ti-search paragraph-p3"></i>
            <PInputText
              placeholder="Search members"
              data-cy="search-members-field"
              v-model="projectStore.accessSearch"
              class="w-full"
            />
          </span>
          <PButton
            v-if="allowShare"
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
import { computed, watchEffect } from 'vue'

import { ProjectMembersTable } from '../components'
import ProjectAccessRequests from '../components/ProjectAccessRequests.vue'
import { useProjectStore } from '../store'

import AppContainer from '@/common/components/AppContainer.vue'
import AppMenu from '@/common/components/AppMenu.vue'
import AppSection from '@/common/components/AppSection.vue'
import { useUserStore } from '@/main'

defineEmits<{ share: [] }>()
withDefaults(
  defineProps<{ showAccessRequests?: boolean; allowShare?: boolean }>(),
  {
    showAccessRequests: false,
    allowShare: true
  }
)

const projectStore = useProjectStore()
const userStore = useUserStore()

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

// Every dashboard table have to load data on orkspace change
watchEffect(() => {
  if (userStore.isWorkspaceAdmin()) {
    projectStore.initNamespaceAccessRequests({
      namespace: userStore.currentWorkspace.name,
      params: null
    })
  }
})
</script>

<style lang="scss" scoped></style>
