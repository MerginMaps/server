<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="displayedChangeset"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="displayedChangeset.length <= 10"
    >
      <!-- headers -->
      <template v-slot:header.insert="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Added</span>
        </v-tooltip>
      </template>
      <template v-slot:header.delete="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Deleted</span>
        </v-tooltip>
      </template>
      <template v-slot:header.update="{ header }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <v-icon v-on="on" small :color="header.color"
              >{{ header.icon }}
            </v-icon>
          </template>
          <span>Modified</span>
        </v-tooltip>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'file-changeset-summary-table',
  props: {
    changesets: Array
  },
  data() {
    return {
      headers: [
        { text: 'Table', value: 'table' },
        {
          text: 'Inserts',
          icon: 'add_circle',
          color: 'green',
          value: 'insert'
        },
        { text: 'Updates', icon: 'edit', color: 'orange', value: 'update' },
        { text: 'Deletes', icon: 'delete', color: 'red', value: 'delete' }
      ]
    }
  },
  computed: {
    displayedChangeset() {
      // Displayed changesets data into table data
      return this.changesets.filter((p) => p.table !== 'gpkg_contents')
    }
  }
})
</script>

<style lang="scss" scoped></style>
