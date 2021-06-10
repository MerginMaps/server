# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="no-shrink column">
    <v-data-table
      :headers="header"
      :items="users"
      no-data-text="No users"
      :hide-default-footer="users.length < 10"
      hide-default-header
      :footer-props="{
        itemsPerPageOptions: [10],
      }"
    >
      <template v-slot:header="{ props: { headers } }">
        <thead class="v-data-table-header">
        <tr>
          <th v-bind:key="header.value" v-for="header in headers">
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
          <v-tooltip top v-if="item.profile.first_name || item.profile.last_name">
            <template v-slot:activator="{ on }">
            <b v-on="on">
              {{ item.username }}
            </b>
            </template>
            <span>
              <span v-if="item.profile.first_name">{{ item.profile.first_name }}</span>
              <span v-if="item.profile.last_name"> {{ item.profile.last_name }}</span>
            </span>
          </v-tooltip>
          <b v-else>
            {{ item.username }}
          </b>
        </td>
        <td>
          <v-select
            v-if="editable(item)"
            :value="item.permission"
            :items="permissionStates"
            @input="e => valueChanged(item, e)"
            hide-details
            label="Select"
            single-line
            class="input-selection"
            style="width: 120px"
          >
          </v-select>
          <span v-else>
            {{ item.permission }}
          </span>
        </td>
        <td class="justify-center layout px-0">
          <v-btn
            :disabled="!editable(item)"
            @click="removeUser(item)"
            icon
          >
            <v-icon color="red darken-3">delete</v-icon>
          </v-btn>
        </td>
      </tr>
      </template>
    </v-data-table>
    <br>
    <div v-if="isAdmin">
      <h3>Invitations</h3>
      <v-data-table
        :headers="headerInvitations"
        :items="invitations"
        no-data-text="No users"
        hide-default-footer
        hide-default-header
      >
        <template v-slot:header="{ props: { headers } }">
          <thead>
          <tr>
            <th v-bind:key="header.value" v-for="header in headers" >
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
          <b>
            {{ item.username }}
          </b>
        </td>
        <td>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
            <span v-on="on">{{ item.expire | remainingtime }}</span>
            </template>
            <span>{{ item.expire | datetime }}</span>
          </v-tooltip>
        </td>
        <td style="text-align: end;">
          <v-chip
            @click="removeInvitation(item)"
            elevation="0"
            color="red"
            small
            class="white--text"
          >
            remove
          </v-chip>
        </td>
      </tr>
      </template>
    </v-data-table>

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
            class="primary white--text"
          :disabled="!user"
          @click="createInvitation"
        >
          <v-icon class="mr-2">add_circle</v-icon>
          Invite
        </v-btn>
      </v-layout>
    </div>
  </v-layout>
</template>

<script>
import debounce from 'lodash/debounce'
import union from 'lodash/union'
import difference from 'lodash/difference'
import concat from 'lodash/concat'
import chunk from 'lodash/chunk'
import OrganisationMixin from '../../mixins/Organisation'
import { mapState } from 'vuex'

export default {
  mixins: [OrganisationMixin],
  props: {
    organisation: Object,
    appUser: Object
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
          align: 'start',
          sortable: false
        },
        {
          text: 'Permission',
          align: 'end',
          sortable: false,
          width: '60',
          tooltip: 'Permission selection for the user'
        },
        {
          text: '',
          align: 'end',
          sortable: false
        }
      ],
      isOwner: false,
      isAdmin: false,
      headerInvitations: [
        {
          text: 'User',
          align: 'start',
          sortable: false
        },
        {
          text: 'Expire in',
          align: 'start',
          sortable: false,
          width: '180',
          tooltip: 'Invitation expiration'
        },
        {
          text: '',
          align: 'end',
          sortable: false
        }
      ]
      // invitations: []
    }
  },
  computed: {
    ...mapState({ invitations: 'orgInvitations' }),
    permissionStates () {
      const states = ['owner', 'admin', 'writer', 'reader']
      if (!this.isOwner) { states.splice(0, 1) }
      return states
    }
  },
  watch: {
    userQuery: 'search',
    organisation: {
      deep: true,
      immediate: true,
      handler () {
      // computed props are evaluated before we get organisation prop, thus we need to watcher instead
        const access = {
          owner: this.organisation.owners,
          admin: difference(this.organisation.admins, this.organisation.owners),
          writer: difference(this.organisation.writers, concat(this.organisation.owners, this.organisation.admins)),
          reader: difference(this.organisation.readers, concat(this.organisation.owners, this.organisation.admins, this.organisation.writers))
        }
        for (const [permission, names] of Object.entries(access)) {
        // server returns only 5 entries from db for single call
          const chunks = chunk(names, 5)
          Promise.all(chunks.map(async (item) => {
            const params = { names: item.join(',') }
            await this.$http.get('/auth/user/search', { params }).then(resp => {
              resp.data
                .filter(i => !this.users.map(u => u.username).includes(i.username))
                .map(i => {
                  i.permission = permission
                  this.users.push(i)
                })
            })
          }))
        }
        this.isOwner = this.organisation.owners.includes(this.appUser.username)
        this.isAdmin = this.isOwner || this.organisation.admins.includes(this.appUser.username)
      }
    }

  },
  created () {
    if (this.isAdmin) { this.getInvitations('org', this.organisation.name) }
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
          const omitUsers = this.users.map(i => i.username)
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
    createInvitation () {
      this.searchResults = []
      this.inviteUser(this.organisation.name, this.user.value.username)
    },
    removeUser (user) {
      this.users.splice(this.users.indexOf(user), 1)
      this.valueChanged()
    },
    emphasizeMatch (string, reg) {
      const res = string.replace(new RegExp(reg, 'i'), function (str) { return '<b>' + str + '</b>' })
      return res
    },
    valueChanged (user, permission) {
      if (user && permission) {
        this.users[this.users.indexOf(user)].permission = permission
      }
      const access = {}
      const permissions = ['owner', 'admin', 'writer', 'reader']
      permissions.forEach(p => {
        access[p] = this.users.filter(u => u.permission === p).map(u => u.username)
      })
      // server requires explicit permissions lists
      this.$emit('save-organisation', {
        owners: access.owner,
        admins: union(access.owner, access.admin),
        writers: union(access.owner, access.admin, access.writer),
        readers: union(access.owner, access.admin, access.writer, access.reader)
      })
    },
    editable (user) {
      if (user.permission === 'owner') {
        // allow edit/remove owner only if there are more than one
        return this.isOwner && this.organisation.owners.length > 1
      } else {
        return this.isAdmin
      }
    },
    getUserProfileName (user) {
      const firstName = user.profile.first_name ? user.profile.first_name : ''
      const lastName = user.profile.last_name ? user.profile.last_name : ''
      return firstName || lastName ? `(${firstName} ${lastName})` : ''
    }
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
.input-selection{
  padding: 0;
  font-size: 12px;
}
</style>
