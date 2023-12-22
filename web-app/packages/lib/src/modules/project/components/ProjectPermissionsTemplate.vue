<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <AppContainer>
    <AppSection>
      <PDataView
        :value="displayedValues"
        :data-key="'id'"
        data-cy="project-verision-table"
        lazy
        :pt="{
          header: {
            // small header
            class: 'px-3 py-2'
          }
        }"
      >
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
            class="flex align-items-center hover:bg-gray-50 cursor-pointer border-bottom-1 border-gray-200 text-sm px-3 py-2 mt-0"
            @click.prevent="rowClick(item.name)"
          >
            <div class="flex-grow-1 grid grid-nogutter">
              <!-- Columns, we are using data view instead table, it is better handling of respnsive state -->
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
                  {{ item[col.value] }}
                </span>
              </div>
              <!-- actions -->
            </div>
            <div class="flex flex-shrink-0 justify-content-end">
              <PButton
                icon="ti ti-download"
                severity="secondary"
                text
                :disabled="!canRemoveUser(item.user.id)"
                @click.stop="removeUser(item.user)"
              />
            </div>
          </div>
        </template>
        <template #empty>
          <div class="w-full text-center p-4">
            <span>No versions found.</span>
          </div>
        </template>
      </PDataView>
    </AppSection>

    <!-- <v-data-table
      :headers="columns"
      :items="displayedValues"
      no-data-text="No users"
      :hide-default-footer="displayedValues.length <= 10"
    >
      <template #header.permissions="{ header }">
        <v-tooltip v-if="header.tooltip" location="top">
          <template v-slot:activator="{ props }">
            <span v-bind="props">
              {{ header.text }}
            </span>
          </template>
          <span>
            {{ header.tooltip }}
          </span>
        </v-tooltip>
        <span v-else>
          {{ header.text }}
        </span>
      </template>

      <template #item.user="{ modelValue }">
        <v-tooltip
          location="top"
          v-if="modelValue.profile.first_name || modelValue.profile.last_name"
        >
          <template v-slot:activator="{ props }">
            <b v-bind="props">
              {{ modelValue.username }}
            </b>
          </template>
          <span>
            <span v-if="modelValue.profile.first_name">{{
              modelValue.profile.first_name
            }}</span>
            <span v-if="modelValue.profile.last_name">
              {{ modelValue.profile.last_name }}</span
            >
          </span>
        </v-tooltip>
        <b v-else>
          {{ modelValue.username }}
        </b>
      </template>

      <template #item.permissions="{ item }">
        <v-select
          :model-value="actualPermissions(item)"
          :items="permissionStates"
          @update:model-value="(e) => valueChanged(item, e)"
          :disabled="!isProjectOwner"
          hide-details
          label="reader"
          single-line
          class="input-selection"
          style="width: 120px"
        >
        </v-select>
      </template>

      <template #item.remove="{ item }">
        <div class="justify-center px-0">
          <v-btn
            :disabled="!canRemoveUser(item.user.id)"
            @click="removeUser(item.user)"
            icon
          >
            <v-icon color="red darken-3">delete</v-icon>
          </v-btn>
        </div>
      </template>
    </v-data-table> -->
    <slot name="banner" />
    <button
      ref="hidden-input"
      id="change-permissions-input"
      style="visibility: hidden"
    />
  </AppContainer>
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

import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'
import { UserSearchParams } from '@/modules/user/types'
import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'

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
          cols: 10
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
    ...mapState(useProjectStore, [
      'currentNamespace',
      'project',
      'isProjectOwner'
    ]),
    permissionStates() {
      return ['owner', 'writer', 'reader']
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
      const el = this.$refs['hidden-input']
      el.value = permission
      el.dispatchEvent(new Event('click', {}))
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
      return ''
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
        ...pick(this.value, [
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
  components: { AppContainer, AppSection }
})
</script>

<style lang="scss" scoped>
.no-shrink {
  flex: 0 0 auto;
}

label {
  font-weight: 500;
}

:deep(*) .v-data-table__overflow {
  margin: 0.5em 0;
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: 0.5em;
  background-color: #f9f9f9;

  .v-datatable {
    background-color: transparent;
  }
}

.v-list {
  :deep(.v-list-item) {
    min-height: unset;
  }
}

.div {
  b {
    margin-right: 10px;
  }

  span {
    margin-right: 3px;
    font-size: 12px;
  }
}

.private-public-btn {
  font-size: 12px;
  padding-left: 20px;
  padding-right: 20px;

  span {
    font-weight: 700;
  }
}

.private-public-text {
  font-size: 14px;
}

.public-private-zone {
  margin-top: 20px;
  margin-bottom: 20px;

  button {
    margin-right: 20px;
    margin-top: 1px;
  }
}
</style>
