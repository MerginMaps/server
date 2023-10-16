<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout class="no-shrink column">
    <label class="mt-4 grey--text text--darken-1">Manage Access:</label>
    <slot name="banner" />
    <v-data-table
      :headers="header"
      :items="displayedValues"
      no-data-text="No users"
      :hide-default-footer="displayedValues.length <= 10"
    >
      <template #header.permissions="{ header }">
        <v-tooltip v-if="header.tooltip" top>
          <template v-slot:activator="{ on }">
            <span v-on="on">
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

      <template #item.user="{ value }">
        <v-tooltip
          top
          v-if="value.profile.first_name || value.profile.last_name"
        >
          <template v-slot:activator="{ on }">
            <b v-on="on">
              {{ value.username }}
            </b>
          </template>
          <span>
            <span v-if="value.profile.first_name">{{
              value.profile.first_name
            }}</span>
            <span v-if="value.profile.last_name">
              {{ value.profile.last_name }}</span
            >
          </span>
        </v-tooltip>
        <b v-else>
          {{ value.username }}
        </b>
      </template>

      <template #item.permissions="{ item }">
        <v-select
          :value="actualPermissions(item)"
          :items="permissionStates"
          @input="(e) => valueChanged(item, e)"
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
    </v-data-table>
    <button
      ref="hidden-input"
      id="change-permissions-input"
      style="visibility: hidden"
    />
  </v-layout>
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

export default defineComponent({
  props: {
    value: Object
  },
  data() {
    return {
      // search data
      isLoading: false,
      users: [],
      header: [
        {
          text: 'User',
          value: 'user',
          align: 'left',
          sortable: false
        },
        {
          text: 'Permissions',
          value: 'permissions',
          width: 60,
          align: 'left',
          sortable: false,
          tooltip: 'Has permission to change project settings'
        },
        {
          text: 'Remove',
          value: 'remove',
          align: 'right',
          sortable: false,
          width: 60
        }
      ],
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
      const { ownersnames, readersnames, writersnames } = this.value
      const users = this.users.map((user) => ({
        username: user.username,
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
    this.originalValue = JSON.parse(JSON.stringify(this.value))
    // this is just temporary solution for ESLint: Unexpected mutation of &quot;value&quot; prop. (vue/no-mutating-props)
    this.clonedValue = JSON.parse(JSON.stringify(this.value))
  },
  watch: {
    value: {
      deep: true,
      handler(value) {
        // update local clonedValue if value is changed in parent
        if (value) {
          this.clonedValue = JSON.parse(JSON.stringify(this.value))
          this.emit()
        }
      }
    },
    users: {
      immediate: true,
      deep: true,
      handler(_access) {
        const { ownersnames, readersnames, writersnames } = this.value
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
        JSON.stringify({ ...this.value, ...modifiedValues })
      )
    }
  }
})
</script>

<style lang="scss" scoped>
.no-shrink {
  flex: 0 0 auto;
}

label {
  font-weight: 500;
}

::v-deep(*) {
  .v-data-table__overflow {
    margin: 0.5em 0;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 0.5em;
    background-color: #f9f9f9;

    .v-datatable {
      background-color: transparent;
    }
  }
}

.v-list {
  ::v-deep(.v-list-item) {
    min-height: unset;
  }
}

.v-list-item-content {
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
