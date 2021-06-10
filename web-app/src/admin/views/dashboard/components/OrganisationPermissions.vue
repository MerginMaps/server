# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <v-layout class="no-shrink column">
  <v-data-table
      :headers="header"
      :items="organisation.readers"
      no-data-text="No users"
      hide-default-footer
      hide-default-header
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
          <b>
            {{ item }}
          </b>
        </td>
        <td>
            {{ rights(item) }}
        </td>
      </tr>
      </template>
    </v-data-table>
    </v-layout>
</template>

<script>
import { mapState } from 'vuex'
import OrganisationMixin from '@/mixins/Organisation'
export default {
  name: 'OrganisationPermissions',
  mixins: [OrganisationMixin],
  props: {
    name: String
  },
  computed: {
    ...mapState(['organisation'])
  },
  data () {
    return {
      header: [
        {
          text: 'User',
          align: 'left',
          sortable: false
        },
        {
          text: 'Permission',
          align: 'left',
          sortable: false,
          width: '180',
          tooltip: 'Permission selection for the user'
        }
      ]
    }
  },
  created () {
    if (!this.organisation || this.organisation.name !== this.name) {
      this.getOrganisation(this.name)
    }
  },
  methods: {
    rights (username) {
      if (this.organisation.owners.includes(username)) {
        return 'owner'
      } else if (this.organisation.admins.includes(username)) {
        return 'admin'
      } else if (this.organisation.writers.includes(username)) {
        return 'writer'
      } else {
        return 'reader'
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
.input-selection{
  padding: 0;
  font-size: 12px;
}
</style>
