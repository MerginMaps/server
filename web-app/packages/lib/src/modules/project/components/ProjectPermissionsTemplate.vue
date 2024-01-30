<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <AppContainer>
      <AppSection>
        <PDataView :value="displayedValues" :data-key="'id'" data-cy="permission-table">
          <template #header>
            <div class="w-11 grid grid-nogutter">
              <!-- Visible on lg breakpoint > -->
              <div
                v-for="col in columns.filter((item) => !item.fixed)"
                :class="['text-xs hidden lg:flex', `col-${col.cols ?? 4}`]"
                :key="col.text"
              >
                {{ col.text }}
              </div>
              <!-- else -->
              <div class="col-12 flex lg:hidden">Members</div>
            </div>
          </template>

          <!-- table rows -->
          <template #list="slotProps">
            <div
              v-for="item in slotProps.items"
              :key="item.id"
              class="flex align-items-center hover:bg-gray-50 border-bottom-1 border-gray-200 text-sm px-4 py-2 mt-0"
            >
              <div class="w-11 grid grid-nogutter">
                <!-- Columns, we are using data view instead table, it is better handling of responsive state -->
                <div
                  v-for="col in columns.filter((item) => !item.fixed)"
                  :key="col.value"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 4}`
                  ]"
                >
                  <p class="text-xs opacity-80 mb-1 lg:hidden">
                    {{ col.text }}
                  </p>
                  <span :class="col.textClass">
                    <PAvatar
                      v-if="col.value === 'email'"
                      :label="(item.username ?? '').charAt(0).toUpperCase()"
                      shape="circle"
                      :pt="{
                        root: {
                          class:
                            'surface-ground mr-2 font-semibold text-color-forest',
                          style: {
                            borderRadius: '50%'
                          }
                        }
                      }"
                    />
                    <AppDropdown
                      v-if="col.value === 'permissions'"
                      :options="permissionStates"
                      :model-value="actualPermissions(item)"
                      @update:model-value="(e) => valueChanged(item, e)"
                      :disabled="
                        item.user.id === loggedUser.id ||
                        item.user.id === project.creator
                      "
                      class="w-6 lg:w-full"
                    />
                    <template v-else
                      >{{ item[col.value] }}
                      <span
                        v-if="
                          col.value === 'email' &&
                          item.user.id === loggedUser.id
                        "
                        >(me)</span
                      ></template
                    >
                  </span>
                </div>
                <!-- actions -->
              </div>
              <div class="w-1 flex justify-content-end">
                <PButton
                  icon="ti ti-trash"
                  rounded
                  plain
                  text
                  @click.stop="removeUser(item.user)"
                  class="text-xl p-0"
                  :style="{
                    visibility: canRemoveUser(item.user.id)
                      ? 'visible'
                      : 'hidden'
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
      </AppSection>
    </AppContainer>
    <AppContainer v-if="$slots.banner"><slot name="banner" /></AppContainer>
  </div>
</template>

<script lang="ts">
import chunk from 'lodash/chunk'
import difference from 'lodash/difference'
import isEqual from 'lodash/isEqual'
import pick from 'lodash/pick'
import sortBy from 'lodash/sortBy'
import toLower from 'lodash/toLower'
import union from 'lodash/union'
import { mapState, mapActions } from 'pinia'
import { defineComponent } from 'vue'

import AppContainer from '@/common/components/AppContainer.vue'
import AppDropdown from '@/common/components/AppDropdown.vue'
import AppSection from '@/common/components/AppSection.vue'
import { DropdownOption } from '@/common/components/types'
import {
  isAtLeastProjectRole,
  ProjectRole,
  ProjectRoleName
} from '@/common/permission_utils'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'
import { UserSearchParams } from '@/modules/user/types'

interface ColumnItem {
  text: string
  value: string
  cols?: number
  fixed?: boolean
  textClass?: string
}

export default defineComponent({
  props: {
    modelValue: Object
  },
  data() {
    return {
      // search data
      isLoading: false,
      users: [],
      columns: [
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
          value: 'permissions',
          cols: 2
        },
        {
          text: 'Remove',
          value: 'remove',
          fixed: true
        }
      ] as ColumnItem[],
      originalValue: null,
      clonedValue: null
    }
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['currentNamespace', 'project']),
    permissionStates(): DropdownOption<ProjectRoleName>[] {
      return [
        {
          value: 'reader',
          label: 'Read only',
          description: 'Can view project files'
        },
        {
          value: 'writer',
          label: 'Write',
          description: 'Can edit project files'
        },
        {
          value: 'owner',
          label: 'Manage',
          description: 'Can share and remove project'
        }
      ]
    },
    displayedValues() {
      const { ownersnames, readersnames, writersnames } = this.modelValue
      const users = this.users.map((user) => ({
        username: user.username,
        email: user.email,
        user,
        owner: ownersnames?.includes(user.username),
        read: readersnames?.includes(user.username),
        write: writersnames?.includes(user.username)
      }))
      return sortBy(users, [
        (u) => {
          return toLower(u.username)
        }
      ])
    }
  },
  created() {
    this.originalValue = JSON.parse(JSON.stringify(this.modelValue))
    // this is just temporary solution for ESLint: Unexpected mutation of &quot;value&quot; prop. (vue/no-mutating-props)
    this.clonedValue = JSON.parse(JSON.stringify(this.modelValue))
  },
  watch: {
    value: {
      deep: true,
      handler(value) {
        // update local clonedValue if value is changed in parent
        if (value) {
          this.clonedValue = JSON.parse(JSON.stringify(this.modelValue))
          this.emit()
        }
      }
    },
    users: {
      immediate: true,
      deep: true,
      handler(_access) {
        const { ownersnames, readersnames, writersnames } = this.modelValue
        const names = union(ownersnames, readersnames, writersnames)
        // server returns only 5 entries from db for single call
        const chunks = chunk(names, 5)
        Promise.all(
          chunks.map(async (item) => {
            const params: UserSearchParams = {
              namespace: this.currentNamespace,
              names: item.join(',')
            }
            await this.getAuthUserSearch(params).then((resp) => {
              resp.data
                .filter(
                  (i) => !this.users.map((u) => u.username).includes(i.username)
                )
                .forEach((i) => this.users.push(i))
            })
          })
        )
      }
    }
  },
  methods: {
    ...mapActions(useUserStore, ['getAuthUserSearch']),
    canRemoveUser(userId: number) {
      // project owner can remove project, but project creator cannot be removed
      return (
        this.project.creator !== userId &&
        isAtLeastProjectRole(this.project.role, ProjectRole.owner)
      )
    },
    valueChanged(user, permission) {
      if (permission === 'owner') {
        this.setOwnerPermission(user)
      } else if (permission === 'writer') {
        this.setWritePermission(user)
      } else if (permission === 'reader') {
        this.setReadPermission(user)
      }
    },
    actualPermissions(item) {
      if (this.project.access.owners.includes(item.user.id)) {
        return 'owner'
      } else if (this.project.access.writers.includes(item.user.id)) {
        return 'writer'
      } else if (this.project.access.readers.includes(item.user.id)) {
        return 'reader'
      }
      return undefined
    },
    removeUser(user) {
      // remove user.username from owners, writers and readers
      const permissionNames = ['ownersnames', 'writersnames', 'readersnames']
      permissionNames.forEach((key) => {
        this.clonedValue[key] = difference(this.clonedValue[key], [
          user.username
        ])
      })
      // emit change of value
      this.emit(this.clonedValue)
      this.users.splice(this.users.indexOf(user), 1)
    },
    setWritePermission(user) {
      this.clonedValue.ownersnames = difference(this.clonedValue.ownersnames, [
        user.username
      ])
      this.clonedValue.writersnames = union(this.clonedValue.writersnames, [
        user.username
      ])
      this.clonedValue.readersnames = union(this.clonedValue.readersnames, [
        user.username
      ])
      // emit change of value
      this.emit(this.clonedValue)
    },
    setOwnerPermission(user) {
      this.clonedValue.ownersnames = union(this.clonedValue.ownersnames, [
        user.username
      ])
      this.clonedValue.writersnames = union(this.clonedValue.writersnames, [
        user.username
      ])
      this.clonedValue.readersnames = union(this.clonedValue.readersnames, [
        user.username
      ])
      // emit change of value
      this.emit(this.clonedValue)
    },
    setReadPermission(user) {
      this.clonedValue.ownersnames = difference(this.clonedValue.ownersnames, [
        user.username
      ])
      this.clonedValue.writersnames = difference(
        this.clonedValue.writersnames,
        [user.username]
      )
      this.clonedValue.readersnames = union(this.clonedValue.readersnames, [
        user.username
      ])
      // emit change of value
      this.emit(this.clonedValue)
    },
    emit(newValues = undefined) {
      const modifiedValues = pick(newValues, [
        'ownersnames',
        'writersnames',
        'readersnames'
      ])
      const current = {
        ...pick(this.modelValue, [
          'ownersnames',
          'writersnames',
          'readersnames',
          'public'
        ]),
        ...modifiedValues
      }
      const original = pick(this.originalValue, [
        'ownersnames',
        'writersnames',
        'readersnames',
        'public'
      ])
      // check if there is actual change (e.g. after refresh from previous server response)
      if (isEqual(original, current)) {
        return
      }
      this.$emit('save-project', newValues)
      this.originalValue = JSON.parse(
        JSON.stringify({ ...this.modelValue, ...modifiedValues })
      )
    }
  },
  components: { AppContainer, AppSection, AppDropdown }
})
</script>

<style lang="scss" scoped></style>
