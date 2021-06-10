# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
    <v-data-table
      :headers="header"
      :items="displayedOrganisations"
      no-data-text="No organisations"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="displayedOrganisations.length <= 10"
      :options="options"
      v-model="selected"
      item-key="name"
    >
            <template v-slot:item="{ item }">
      <tr>

        <td>
          <router-link :to="{ name: 'org_profile', params: { name: item.name }}">
              {{ item.name }}
          </router-link>
        </td>
        <td>
          <v-icon v-if="item.active" color="green">check</v-icon>
          <v-icon v-else color="red">remove</v-icon>
        </td>
        <td>{{ item.description }}</td>
        <td>
          <router-link :to="{ name: 'namespace-projects', params: { namespace: item.name }}">
            {{ item.project_count }}
          </router-link>
        </td>
        <td>{{ item.disk_usage | filesize }}</td>
        <td>{{ item.storage | filesize }}</td>
        <td>{{ item.role }}</td>
      </tr>
            </template>
    </v-data-table>
</template>

<script>
import escapeRegExp from 'lodash/escapeRegExp'
import { removeAccents, downloadJsonList } from '../util'
import OrganisationMixin from '../mixins/Organisation'
import { mapState } from 'vuex'


export default {
  name: 'organisations-table',
  mixins: [
    OrganisationMixin
  ],
  props: {
    username: String
  },
  data () {
    return {
      options: {
        'sort-by': 'name'
      },
      selected: [],
      header: [
        { text: 'Name', value: 'name' },
        { text: 'Active', value: 'active' },
        { text: 'Description', value: 'description' },
        { text: 'Projects', value: 'project_count' },
        { text: 'Usage', value: 'disk_usage' },
        { text: 'Storage', value: 'storage' },
        { text: 'Role', value: 'role' }
      ],
      searchFilter: ''
    }
  },
  computed: {
    ...mapState(['organisations', 'app']),
    displayedOrganisations () {
      let organisations = this.organisations
      if (this.searchFilter) {
        const regex = new RegExp(escapeRegExp(removeAccents(this.searchFilter.trim())), 'i')
        organisations = organisations.filter(
          o => (o.name.search(regex) !== -1)
        )
      }
      return organisations
    }
  },
  created () {
    this.getUserOrganisations()
  },
  methods: {
    exportList () {
      downloadJsonList(this.selected, this.header, 'organisations')
    },
    removeSelected () {
      const promises = this.selected.map(org => { return this.deleteOrganisation(org.name) })
      Promise.all(promises)
        .then()
        .catch(err => {
          const msg = (err.response && err.response.status === 503) ? err.response.data.detail : 'Unable to remove organisations'
          this.$notification.error(msg)
        })
    }
  }
}
</script>

<style lang="scss" scoped>
.v-data-table {
  td {
    text-align: left;
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
