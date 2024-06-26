<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <app-section>
      <PDataView
        :value="searchedItems"
        :rows="itemsPerPage"
        :paginator="searchedItems.length > itemsPerPage"
        :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
        :data-key="'id'"
        data-cy="permission-table"
        :sortField="projectStore.accessSorting?.sortBy"
        :sortOrder="projectStore.accessSorting?.sortDesc ? -1 : 1"
      >
        <template #header>
          <div class="w-11 grid grid-nogutter">
            <!-- Visible on lg breakpoint > -->
            <div
              v-for="col in columns.filter((item) => !item.fixed)"
              :class="['paragraph-p6 hidden lg:flex', `col-${col.cols ?? 4}`]"
              :key="col.text"
            >
              {{ col.text }}
            </div>
            <!-- else -->
            <div class="col-12 flex lg:hidden">Members</div>
          </div>
        </template>

        <!-- table rows -->options
        <template #list="slotProps">
          <div
            v-for="item in slotProps.items"
            :key="item.id"
            class="flex align-items-center hover:bg-gray-50 border-bottom-1 border-gray-200 paragraph-p6 px-4 py-2 mt-0"
          >
            <div class="w-11 grid grid-nogutter">
              <!-- Columns, we are using data view instead table, it is better handling of responsive state -->
              <div
                v-for="col in columns.filter((item) => !item.fixed)"
                :key="col.value"
                :class="[
                  'flex flex-column justify-content-center col-12 gap-1 py-2',
                  `lg:col-${col.cols ?? 4}`,
                  'lg:py-0'
                ]"
              >
                <p class="opacity-80 lg:hidden font-semibold">
                  {{ col.text }}
                </p>
                <div
                  :class="[
                    col.textClass || 'opacity-80',
                    // Center texts with additional content Avatar - text
                    'flex align-items-center'
                  ]"
                >
                  <PAvatar
                    v-if="col.value === 'email'"
                    :label="$filters.getAvatar(item.email, item.name)"
                    shape="circle"
                    :pt="{
                      root: {
                        class:
                          'mr-2 font-semibold text-color-forest flex-shrink-0',
                        style: {
                          borderRadius: '50%'
                        }
                      }
                    }"
                  />
                  <AppDropdown
                    v-if="col.value === 'roles'"
                    :options="roles"
                    :model-value="item.project_permission"
                    @update:model-value="(e) => roleUpdate(item, e)"
                    :disabled="item.id === loggedUser.id"
                    class="w-6 lg:w-full"
                  />
                  <span v-else
                    >{{ item[col.value] }}
                    <template
                      v-if="col.value === 'email' && item.id === loggedUser.id"
                      >(me)</template
                    ></span
                  >
                </div>
              </div>
              <!-- actions -->
            </div>
            <div class="w-1 flex justify-content-end">
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
            </div>
          </div>
        </template>
        <template #empty>
          <div class="w-full text-center p-4">
            <span>No members found.</span>
          </div>
        </template>
      </PDataView>
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
import {
  GlobalRole,
  ProjectRoleName,
  isAtLeastGlobalRole
} from '@/common/permission_utils'
import { useInstanceStore, useUserStore } from '@/main'

// TODO: Externalize to AppCol element
interface ColumnItem {
  text: string
  value: string
  cols?: number
  fixed?: boolean
  textClass?: string
}

interface Props {
  allowRemove?: boolean
}

const projectStore = useProjectStore()
const userStore = useUserStore()
const instanceStore = useInstanceStore()

const props = withDefaults(defineProps<Props>(), { allowRemove: true })

const itemsPerPage = ref(10)
const columns = ref<ColumnItem[]>([
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
    data: { role: value, user_id: item.id }
  })
}

onUnmounted(() => {
  projectStore.access = []
})

projectStore.getProjectAccess(projectStore.project?.id)
</script>

<style scoped lang="scss"></style>
