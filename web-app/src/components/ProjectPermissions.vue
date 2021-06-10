# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="no-shrink column">
    <label class="mt-4 grey--text text--darken-1">Manage Access:</label>
    <v-data-table
        :headers="header"
        :items="displayedValues"
        no-data-text="No users"
        hide-default-header
        :hide-default-footer="displayedValues.length <= 10"
    >
      <template v-slot:header="{ props: { headers } }">
        <thead>
        <tr>
          <th v-bind:key="header.text" v-for="header in headers" :style="`width: ${header.width}px`">
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
          </th>
        </tr>
        </thead>
      </template>

      <template v-slot:item="{ item }">
        <tr>
          <td>
            <v-tooltip top v-if="item.user.profile.first_name || item.user.profile.last_name">
              <template v-slot:activator="{ on }">
              <b v-on="on">
                {{ item.user.username }}
              </b>
              </template>
              <span>
              <span v-if="item.user.profile.first_name">{{ item.user.profile.first_name }}</span>
              <span v-if="item.user.profile.last_name"> {{ item.user.profile.last_name }}</span>
            </span>
            </v-tooltip>
            <b v-else>
              {{ item.user.username }}
            </b>
          </td>
          <td>
            <v-select
            :value="actualPermissions(item)"
            :items="permissionStates"
            @input="e => valueChanged(item, e)"
            :disabled="project.creator === item.user.id || !project.access.owners.includes(app.user.id)"
            hide-details
            label="reader"
            single-line
            class="input-selection"
            style="width: 120px"
          >
          </v-select>
          </td>
          <td class="justify-center px-0">
            <v-btn
                :disabled="project.creator === item.user.id || !project.access.owners.includes(app.user.id)"
                @click="removeUser(item.user)"
                icon
            >
              <v-icon color="red darken-3">delete</v-icon>
            </v-btn>
          </td>
        </tr>
      </template>
    </v-data-table>
    <label class="mt-4 grey--text text--darken-1">Invite collaborators:</label>
    <v-layout mx-3 my-2 align-end>
      <v-autocomplete
        placeholder="Find user"
        v-model="user"
        :loading="isLoading"
        :items="searchResults"
        :search-input.sync="userQuery"
        clearable
        return-object
        no-data-text="Type more letters"
        :hide-no-data="userQuery && userQuery.length > 2"
        hide-details
      >
        <template v-slot:item="{ item }">
            <v-list-item-content style="padding-bottom: 6px; padding-top: 6px;">
              <div v-html="`${emphasizeMatch(item.value.username, userQuery)}  ${getUserProfileName(item.value)}`" class="v-list-item-content">
              </div>
            </v-list-item-content>
      </template>
      </v-autocomplete>
      <v-btn
        id="invite-collaborator-btn"
        class="ml-4 my-0"
        :disabled="!user || !project.access.owners.includes(app.user.id)"
        @click="addUser"
      >
        <v-icon class="mr-2">add_circle</v-icon>
        Add
      </v-btn>
    </v-layout>
    <br>
    <button ref="hidden-input" id="change-permissions-input" style="visibility: hidden"/>
  </v-layout>
</template>

<script>
import debounce from 'lodash/debounce'
import union from 'lodash/union'
import difference from 'lodash/difference'
import chunk from 'lodash/chunk'
import pick from 'lodash/pick'
import isEqual from 'lodash/isEqual'
import sortBy from 'lodash/sortBy'
import toLower from 'lodash/toLower'
import { mapState } from 'vuex'

export default {
  props: {
    value: Object
  },
  data () {
    return {
      // search data
      userQuery: '',
      isLoading: false,
      searchResults: [],
      user: null,
      users: [],
      header: [
        {
          text: 'User',
          align: 'left',
          sortable: false
        }, {
          text: 'Permissions',
          width: 60,
          align: 'left',
          sortable: false,
          tooltip: 'Has permission to change project settings'
        }, {
          text: 'Remove',
          align: 'right',
          sortable: false,
          width: 60
        }
      ],
      originalValue: null
    }
  },
  computed: {
    ...mapState(['project', 'app']),
    permissionStates () {
      return ['owner', 'writer', 'reader']
    },
    displayedValues () {
      const { ownersnames, readersnames, writersnames } = this.value
      const users = this.users.map(user => ({
        username: user.username,
        user,
        owner: ownersnames.includes(user.username),
        read: readersnames.includes(user.username),
        write: writersnames.includes(user.username)
      }))
      return sortBy(users, [u => { return toLower(u.username) }])
    }
  },
  created () {
    this.originalValue = JSON.parse(JSON.stringify(this.value))
  },
  watch: {
    userQuery: 'search',
    value: {
      deep: true,
      handler () {
        this.emit()
      }
    },
    users: {
      immediate: true,
      deep: true,
      handler (access) {
        const { ownersnames, readersnames, writersnames } = this.value
        const names = union(ownersnames, readersnames, writersnames)
        // server returns only 5 entries from db for single call
        const chunks = chunk(names, 5)
        Promise.all(chunks.map(async (item) => {
          const params = { names: item.join(',') }
          await this.$http.get('/auth/user/search', { params }).then(resp => {
            resp.data
              .filter(i => !this.users.map(u => u.username).includes(i.username))
              .map(i => (this.users.push(i)))
          })
        }))
      }
    }
  },
  methods: {
    search: debounce(function () {
      if (this.user && this.userQuery === this.user.text) {
        return
      }
      if (!this.userQuery || this.userQuery.length < 3) {
        this.searchResults = []
        return
      }
      this.isLoading = true
      const params = { like: this.userQuery }
      this.$http.get('/auth/user/search', { params })
        .then(resp => {
          const omitUsers = this.displayedValues.map(i => i.user.username)
          this.searchResults = resp.data
            .filter(u => !omitUsers.includes(u.username))
            .map(u => ({
              value: u,
              text: u.username
            }))
          this.isLoading = false
        })
        .catch(() => {
          this.isLoading = false
        })
    }, 300),
    addUser () {
      const user = this.user.value
      this.value.readersnames.push(user.username)
      this.users.push(user)
      this.user = null
      this.searchResults = []
    },
    valueChanged (user, permission) {
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
    actualPermissions (item) {
      if (this.project.access.owners.includes(item.user.id)) {
        return 'owner'
      } else if (this.project.access.writers.includes(item.user.id)) {
        return 'writer'
      } else if (this.project.access.readers.includes(item.user.id)) {
        return 'reader'
      }
      return ''
    },
    removeUser (user) {
      // remove user.username from owners, writers and readers
      ['ownersnames', 'writersnames', 'readersnames'].forEach(key => {
        this.value[key] = difference(this.value[key], [user.username])
      })

      this.users.splice(this.users.indexOf(user), 1)
    },
    setWritePermission (user) {
      this.value.ownersnames = difference(this.value.ownersnames, [user.username])
      this.value.writersnames = union(this.value.writersnames, [user.username])
      this.value.readersnames = union(this.value.readersnames, [user.username])
    },
    setOwnerPermission (user) {
      this.value.ownersnames = union(this.value.ownersnames, [user.username])
      this.value.writersnames = union(this.value.writersnames, [user.username])
      this.value.readersnames = union(this.value.readersnames, [user.username])
    },
    emphasizeMatch (string, reg) {
      const res = string.replace(new RegExp(reg, 'i'), function (str) { return '<b>' + str + '</b>' })
      return res
    },
    setReadPermission (user) {
      this.value.ownersnames = difference(this.value.ownersnames, [user.username])
      this.value.writersnames = difference(this.value.writersnames, [user.username])
      this.value.readersnames = union(this.value.readersnames, [user.username])
    },
    getUserProfileName (user) {
      const firstName = user.profile.first_name ? user.profile.first_name : ''
      const lastName = user.profile.last_name ? user.profile.last_name : ''
      return firstName || lastName ? `(${firstName} ${lastName})` : ''
    },
    emit: debounce(function () {
      const current = pick(this.value, ['ownersnames', 'writersnames', 'readersnames', 'public'])
      const original = pick(this.originalValue, ['ownersnames', 'writersnames', 'readersnames', 'public'])
      // check if there is actual change (e.g. after refresh from previous server response)
      if (isEqual(original, current)) { return }
      this.$emit('save-project')
      this.originalValue = JSON.parse(JSON.stringify(this.value))
    }, 2000)
  }
}
</script>

<style lang="scss" scoped>
.no-shrink {
  flex: 0 0 auto;
}
label {
  font-weight: 500;
}
::v-deep {
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
  ::v-deep .v-list-item {
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
