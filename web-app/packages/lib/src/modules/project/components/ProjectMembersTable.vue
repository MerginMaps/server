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

        <template #col-email="{ column, item }">
          <div
            :class="[
              column.textClass,
              // Center texts with additional content Avatar - text
              'flex align-items-center'
            ]"
          >
            <PAvatar
              :label="$filters.getAvatar(item.email, item.name)"
              shape="circle"
              :pt="{
                root: {
                  class: 'mr-2 font-semibold text-color-forest flex-shrink-0',
                  style: {
                    borderRadius: '50%'
                  }
                }
              }"
            />
            <span
              >{{ item[column.value] }}
              <template
                v-if="column.value === 'email' && item.id === loggedUser.id"
                >(me)</template
              ></span
            >
          </div>
        </template>

        <template #col-roles="{ item }">
          <AppDropdown
            :options="roles"
            :model-value="item.project_permission"
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
import { ProjectAccessDetail } from '../types'

import AppContainer from '@/common/components/AppContainer.vue'
import AppDropdown from '@/common/components/AppDropdown.vue'
import AppSection from '@/common/components/AppSection.vue'
import DataViewWrapper from '@/common/components/data-view/DataViewWrapper.vue'
import { DataViewWrapperColumnItem } from '@/common/components/data-view/types'
import {
  GlobalRole,
  ProjectRoleName,
  isAtLeastGlobalRole
} from '@/common/permission_utils'
import { useInstanceStore, useUserStore } from '@/main'

interface Props {
  allowRemove?: boolean
}

const projectStore = useProjectStore()
const userStore = useUserStore()
const instanceStore = useInstanceStore()

const props = withDefaults(defineProps<Props>(), { allowRemove: true })

const itemsPerPage = ref(10)
const columns = ref<DataViewWrapperColumnItem[]>([
  {
    text: 'Email address',
    value: 'email',
    textClass: 'font-semibold',
    cols: 5
  },
  {
    text: 'Username',
    value: 'username',
    cols: 5
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
  projectStore.access.filter((item) => {
    return [item.username, item.email].some(
      (v) => v && v.toString().toLowerCase().includes(projectStore.accessSearch)
    )
  })
)

function canRemoveMember(item: ProjectAccessDetail) {
  return props.allowRemove && item.id !== loggedUser.value?.id
}

function removeMember(item: ProjectAccessDetail) {
  projectStore.removeProjectAccess(item)
}

function roleUpdate(item: ProjectAccessDetail, value: ProjectRoleName) {
  projectStore.updateProjectAccess({
    projectId: projectStore.project.id,
    userId: item.id,
    data: { role: value }
  })
}

onUnmounted(() => {
  projectStore.access = []
})

projectStore.getProjectAccess(projectStore.project?.id)
</script>

<style scoped lang="scss"></style>
