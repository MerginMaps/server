# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="no-shrink column">
    <v-layout class="public-private-zone">
      <span class="private-public-text" v-if="value.public">
          <b>This is public project</b><br>
      </span>
      <span class="private-public-text" v-else>
          <b>This is private project</b><br>
      </span>
      <v-spacer/>
    </v-layout>
    <label class="mt-4 grey--text text--darken-1">Members:</label>
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
            <span>
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
              <b >{{ item.permissions }}</b>
          </td>
        </tr>
      </template>
    </v-data-table>
  </v-layout>
</template>

<script>
import sortBy from 'lodash/sortBy'
import toLower from 'lodash/toLower'
import { mapState } from 'vuex'
import union from 'lodash/union'
import chunk from 'lodash/chunk'

export default {
  name: 'AdminProjectPermissions',
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
          sortable: false
        }
      ],
      originalValue: null
    }
  },
  computed: {
    ...mapState(['project', 'app']),
    displayedValues () {
      const { ownersnames, writersnames } = this.value
      const users = this.users.map(user => ({
        username: toLower(user.username),
        user,
        permissions: ownersnames.includes(user.username) ? 'owner' : writersnames.includes(user.username) ? 'writer' : 'reader'
      }))
      return sortBy(users, 'username')
    }
  },
  created () {
    this.originalValue = JSON.parse(JSON.stringify(this.value))
  },
  watch: {
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

.v-list-item-content{
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
