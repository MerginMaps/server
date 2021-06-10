# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-data-table
      :headers="header"
      :items="accessRequests"
      ref="table"
      no-data-text="No access requests"
      color="primary"
      footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
      :hide-default-footer="accessRequests.length <= 10"
      :options="options"
    >
      <template v-slot:item="{ item }">
        <tr>
          <td>
          {{ item.user.username }}
        </td>
        <td>
          {{ item.project_name }}
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
            <v-select
              :items="['read', 'write', 'owner']"
              v-model="permissions[item.id]"
              return-object
              :disabled="item.namespace !== app.user.username"
              >
            </v-select>
          </td>
          <td class="justify-center ">
          <div style="text-align: end">
            <v-tooltip bottom v-if="item.namespace === app.user.username">
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  :disabled="expired(item.expire)"
                  @click="acceptRequest(item)"
                  elevation="0"
                  color="green"
                  class="white--text"
                  :value="permissions[item.id]"
                >
                  accept
                </v-chip>
              </span>
            </template>
              <span>Accept request</span>
            </v-tooltip>
            <v-tooltip bottom>
              <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  @click="cancelRequest(item)"
                  elevation="0"
                  color="red"
                  class="white--text"
                >
                  cancel
                </v-chip>
              </span>
              </template>
              <span>Cancel request</span>
            </v-tooltip>
          </div>
        </td>
      </tr>
      </template>
    </v-data-table>
    <button ref="hidden-btn" id="accept-request-access-btn" style="visibility: hidden"/>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import MerginAPIMixin from '../mixins/MerginAPI'
import { postRetryCond } from '../http'


export default {
  name: 'access-request-table',
  components: { },
  mixins: [MerginAPIMixin],
  data () {
    return {
      options: {
        'sort-by': 'name'
      },
      projectAccessRequests: [],
      permissions: {}
    }
  },
  computed: {
    ...mapState(['app', 'transfers', 'accessRequests']),
    header () {
      return [
        { text: 'Requester', value: 'user.username', sortable: true },
        { text: 'Name', value: 'project_name', sortable: true },
        { text: 'Expire in', value: 'expire', sortable: true },
        { text: 'Permissions', width: 120, sortable: false },
        { text: '', width: 190, sortable: false }
      ]
    }
  },
  created () {
    this.fetchAccessRequests()
    this.accessRequests.forEach(request => {
      this.permissions[request.id] = 'read'
    })
  },
  methods: {
    acceptRequest (request) {
      const el = this.$refs['hidden-btn']
      el.value = this.permissions[request.id]
      el.dispatchEvent(new Event('click', {}))

      const data = {
        permissions: this.permissions[request.id]
      }
      const params = {
        'axios-retry': {
          retries: 5,
          retryCondition: error => postRetryCond(error)
        }
      }
      this.$http.post(`/app/project/accept/request/${request.id}`, data, params)
        .then(resp => {
          this.fetchAccessRequests()
        })
    },
    changeSort (column) {
      if (this.options.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.options.sortBy = column
        this.options.descending = false
      }
    },
    expired (expire) {
      return Date.parse(expire) < Date.now()
    },
    cancelRequest (request) {
      this.cancelProjectAccessRequest(request)
      this.fetchAccessRequests()
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
