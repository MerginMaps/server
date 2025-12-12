<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section>
      <DataViewWrapper
        :data-key="'id'"
        data-cy="permission-table"
        :value="searchedItems"
        :rows="itemsPerPage"
        :columns="columns"
        :paginator="searchedItems.length > itemsPerPage"
        :loading="projectStore.accessLoading"
        :empty-message="'No members found.'"
        :row-cursor-pointer="false"
        :options="{
          itemsPerPage,
          sortBy: projectStore.accessSorting?.sortBy,
          sortDesc: projectStore.accessSorting?.sortDesc
        }"
      >
        <template #header-title>Members</template>
        <template #actions="{ item }">
          <PButton
            icon="ti ti-trash"
            rounded
            plain
            text
            @click.stop="removeMember(item)"
            class="paragraph-p3 p-0"
            :style="{
              visibility: canRemoveMember(item) ? 'visible' : 'hidden'
            }"
          />
        </template>

        <template #col-member="{ column, item }">
          <div
            :class="[
              column.textClass,
              // Center texts with additional content Avatar - text
              'flex align-items-center py-2'
            ]"
          >
            <ProjectMemberItem
              :user="item"
              :is-me="item.id === loggedUser.id"
            />
          </div>
        </template>

        <template #col-roles="{ item }">
          <AppDropdown
            :options="roles"
            :model-value="item.role"
            @update:model-value="(e) => roleUpdate(item, e)"
            :disabled="item.id === loggedUser.id"
            class="w-6 lg:w-full"
          />
        </template>
      </DataViewWrapper>
    </app-section>
  </app-container>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'

import { useProjectStore } from '../store'
import { ProjectCollaborator } from '../types'
import ProjectMemberItem from './UserSummary.vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppDropdown from '@/common/components/AppDropdown.vue'
import AppSection from '@/common/components/AppSection.vue'
import DataViewWrapper from '@/common/components/data-view/DataViewWrapper.vue'
import { DataViewWrapperColumnItem } from '@/common/components/data-view/types'
import {
  GlobalRole,
  ProjectRoleName,
  isAtLeastGlobalRole,
  USER_ROLE_NAME_BY_ROLE,
  WorkspaceRole
} from '@/common/permission_utils'
import { useInstanceStore, useUserStore } from '@/main'

const projectStore = useProjectStore()
const userStore = useUserStore()
const instanceStore = useInstanceStore()

const itemsPerPage = ref(10)
const columns = ref<DataViewWrapperColumnItem[]>([
  {
    text: 'Member',
    value: 'member',
    textClass: 'font-semibold',
    cols: 10
  },
  {
    text: 'Project permissions',
    value: 'roles',
    cols: 2
  },
  {
    text: 'Remove',
    value: 'remove',
    fixed: true
  }
])

// TODO: do not bother with GlobalRole but use workspace_role attribute
const roles = computed(() =>
  projectStore.availableRoles.map((item) => ({
    ...item,
    disabled: !isAtLeastGlobalRole(
      item.value,
      instanceStore.currentGlobalRole ?? GlobalRole.global_read
    )
  }))
)
const loggedUser = computed(() => userStore.loggedUser)
const searchedItems = computed(() =>
  projectStore.collaborators.filter((item) => {
    return [item.username, item.email].some(
      (v) => v && v.toString().toLowerCase().includes(projectStore.accessSearch)
    )
  })
)

function canRemoveMember(item: ProjectCollaborator) {
  return (
    item.workspace_role === USER_ROLE_NAME_BY_ROLE[WorkspaceRole.guest] &&
    item.id !== loggedUser.value?.id
  )
}

function removeMember(item: ProjectCollaborator) {
  projectStore.removeProjectAccess(item)
}

function roleUpdate(item: ProjectCollaborator, value: ProjectRoleName) {
  projectStore.updateProjectCollaborators({
    projectId: projectStore.project.id,
    collaborator: item,
    data: { role: value }
  })
}

onUnmounted(() => {
  projectStore.collaborators = []
})

projectStore.getProjectCollaborators(projectStore.project?.id)
</script>

<style scoped lang="scss"></style>
