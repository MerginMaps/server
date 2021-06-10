# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-data-table
      :headers="header"
      :items="transfers"
      ref="table"
      no-data-text="No transfers"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="transfers.length <= 10"
      :options="options"
    >
      <template v-slot:item="{ item }">
        <tr>
        <td>
          <router-link :to="{name: 'project', params: {namespace: item.project.namespace, projectName: item.project.name}}">
            <strong>{{ item.project_name }}</strong>
          </router-link>
        </td>
        <td>
          {{ item.from_ns_name }}
        </td>
        <td>
          {{ item.to_ns_name }}
        </td>
        <td>
          {{ item.requested_by }}
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
          <div style="text-align: end">
            <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  v-if="!expired(item.expire) && incoming(item)"
                  @click="acceptTransferDialog(item)"
                  elevation="0"
                  color="green"
                  class="white--text"
                >
                  accept
                </v-chip>
              </span>
            </template>
              <span>Accept transfer</span>
            </v-tooltip>
            <v-tooltip bottom>
              <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  @click="cancelTransfer(item)"
                  elevation="0"
                  color="red"
                  class="white--text"
                >
                  cancel
                </v-chip>
              </span>
              </template>
              <span>Cancel transfer</span>
            </v-tooltip>
          </div>
        </td>
      </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import MerginAPIMixin from '../mixins/MerginAPI'
import AcceptProjectTransferForm from '@/components/AcceptProjectTransferForm'

export default {
  name: 'transfers-table',
  components: { },
  mixins: [MerginAPIMixin],
  props: {
    namespace: String
  },
  data () {
    return {
      options: {
        'sort-by': 'name'
      }
    }
  },
  computed: {
    ...mapState(['transfers']),
    header () {
      return [
        { text: 'Name', value: 'project_name', sortable: true },
        { text: 'From owner', value: 'from_ns_name', sortable: true },
        { text: 'To owner', value: 'to_ns_name', sortable: true },
        { text: 'Requested by', value: 'requested_by', sortable: false },
        { text: 'Expire in', value: 'expire', sortable: true },
        { text: '', width: 190, sortable: false }
      ]
    }
  },
  created () {
    this.fetchTransfers(this.namespace)
  },
  methods: {
    changeSort (column) {
      if (this.options.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.options.sortBy = column
        this.options.descending = false
      }
    },
    incoming (transfer) {
      return transfer.to_ns_name === this.namespace
    },
    outcoming (transfer) {
      return transfer.from_ns_name === this.namespace
    },
    expired (expire) {
      return Date.parse(expire) < Date.now()
    },
    acceptTransferDialog (transfer) {
      const dialog = { maxWidth: 500, persistent: true }
      const props = { transfer: transfer }
      this.$dialog.show(AcceptProjectTransferForm, { props, dialog })
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
}
</style>
