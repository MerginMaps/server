# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
     <v-data-table
      :headers="headerInvitations"
      :items="invitations"
      no-data-text="No invitations"
      hide-default-footer
      hide-default-header
      fixed-header
    >
      <template v-slot:header="{ props: { headers } }">
        <thead>
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
          <b>
            {{ item.org_name }}
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
        <td>
          <div v-if="!expired(item.expire)" style="text-align: end">
            <v-chip
              @click="acceptInvitation(item)"
              elevation="0"
              color="green"
              class="white--text"
            >
              accept
            </v-chip>
            <v-chip
              @click="removeInvitation(item)"
              elevation="0"
              color="red"
              class="white--text"
            >
              reject
            </v-chip>
          </div>
        </td>
      </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import OrganisationMixin from '../mixins/Organisation'


import { mapState } from 'vuex'


export default {
  name: 'invitations-table',
  mixins: [
    OrganisationMixin
  ],
  props: {
    username: String
  },
  data () {
    return {
      headerInvitations: [
        {
          text: 'Organisation',
          align: 'start',
          sortable: false
        },
        {
          text: 'Expire in',
          align: 'start',
          sortable: false,
          tooltip: 'Invitation expiration'
        },
        {
          text: '',
          align: 'end',
          sortable: false
        }
      ]
    }
  },
  computed: {
    ...mapState(['invitations'])
  },
  created () {
    this.getInvitations('user', this.username)
  },
  methods: {
    expired (expire) {
      return Date.parse(expire) < Date.now()
    }
  }
}
</script>

<style lang="scss" scoped>
.v-data-table {
  td {
    &.flags {
      .v-icon {
        margin: 0 1px;
        cursor: default;
      }
    }
  }
  a {
    text-decoration: none;
  }
  .v-chip {
    margin: 0;
    margin-right: 0.5em;
    height: 1.6em;
    ::v-deep .v-chip__content {
      cursor: pointer;
      padding: 0 0.5em;
      font-size: 85%;
    }
  }
  .hidden {
    opacity: 0;
    pointer-events: none;
  }
}
</style>
