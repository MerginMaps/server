<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <project-share-template
    v-model="data.permission"
    :permissions="projectStore.availableRoles"
    :disabled="data.isPending || data.selectedUsers.length === 0"
    @close="dialogStore.close"
    @submit="share"
  >
    <template #accountsInput
      ><label class="paragraph-p6" for="accounts">Share with</label
      ><PAutoComplete
        @complete="search"
        v-model="data.selectedUsers"
        multiple
        optionLabel="label"
        :suggestions="data.users"
        :placeholder="
          data.selectedUsers.length ? '' : 'Search users by username or email'
        "
        input-id="accounts"
        data-key="key"
        @item-select="select"
        :minLength="0"
        forceSelection
        completeOnFocus
      >
        <template #option="{ option }">
          <div :key="option.key" class="flex align-items-center gap-4">
            <PAvatar
              :label="$filters.getAvatar((option.value as UserSearch).email, [option.value.profile?.first_name, option.value.profile?.last_name].filter(Boolean).join(' '))"
              shape="circle"
              :pt="{
                root: {
                  class: 'font-semibold text-color-forest mr-2',
                  style: {
                    borderRadius: '50%'
                  }
                }
              }"
            />

            <div class="flex flex-column">
              <span class="tip-message-title title-t3">
                {{ option.value.username }}
              </span>
              <span class="opacity-80 paragraph-p5">
                {{ option.value.email }}
              </span>
            </div>
          </div>
        </template>
        <template #empty>
          <p class="p-2">
            <i class="text-color-forest ti ti-info-circle-filled"></i
            >{{ ' ' }}No matches found - Try using their emails instead
          </p></template
        >
        <template v-if="data.users.length" #footer
          ><p class="px-2">
            <i class="text-color-forest ti ti-info-circle-filled"></i
            >{{ ' ' }}Not the right person? Try typing their email instead
          </p></template
        >
        <template #removetokenicon="slotProps"
          ><i
            class="ti ti-x cursor-pointer"
            @click.stop="slotProps.removeCallback"
        /></template> </PAutoComplete
    ></template>
  </project-share-template>
</template>

<script setup lang="ts">
/**
 * ProjectShareDialog component.
 *
 * Allows sharing a project with other users by adding them to project access.
 * Can find users and update project access.
 */
import { AutoCompleteCompleteEvent } from 'primevue/autocomplete'
import { reactive } from 'vue'

import ProjectShareTemplate from './ProjectShareDialogTemplate.vue'

import { ProjectRoleName } from '@/common/permission_utils'
import { AutoCompleteItem, useUserStore } from '@/main'
import { useDialogStore } from '@/modules/dialog/store'
import { useProjectStore } from '@/modules/project/store'
import { UserSearch, UserSearchParams } from '@/modules/user/types'

interface Data {
  users: AutoCompleteItem<UserSearch>[]
  selectedUsers: AutoCompleteItem<UserSearch>[]
  isPending: boolean
  permission: ProjectRoleName
}

const data = reactive<Data>({
  users: [],
  selectedUsers: [],
  isPending: false,
  permission: 'reader'
})

const emit = defineEmits<{
  onShareError: [error: Error]
}>()

const projectStore = useProjectStore()
const userStore = useUserStore()
const dialogStore = useDialogStore()

const search = async (e: AutoCompleteCompleteEvent) => {
  if (data.isPending) {
    return
  }
  try {
    data.isPending = true
    const params: UserSearchParams = {
      namespace: userStore.currentWorkspace?.name,
      like: e.query
    }
    const response = await userStore.getAuthNotProjectUserSearch(params)
    data.users = response.data.map((item) => ({
      key: item.id,
      value: item,
      label: item.name || item.username
    }))
  } finally {
    data.isPending = false
  }
}

const share = async () => {
  if (!data.selectedUsers.length) return

  const {
    ownersnames,
    readersnames,
    editorsnames,
    writersnames,
    public: publicProject
  } = projectStore.project.access
  try {
    await projectStore.saveProjectAccessByRoleName({
      namespace: userStore.currentWorkspace?.name,
      settings: {
        access: {
          ownersnames,
          readersnames,
          editorsnames,
          writersnames,
          public: publicProject
        }
      },
      userNames: data.selectedUsers.map((item) => item.value.username),
      roleName: data.permission,
      projectName: projectStore.project.name
    })
    await projectStore.getProjectAccess(projectStore.project?.id)
    dialogStore.close()
  } catch (err) {
    emit('onShareError', err as Error)
  }
}

function select(e) {
  const founded = data.selectedUsers.filter((item) => item.key === e.value.key)
  if (founded.length > 1) {
    data.selectedUsers = data.selectedUsers.slice(0, -1)
  }
}
</script>
