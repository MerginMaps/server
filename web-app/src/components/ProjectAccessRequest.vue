# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-layout class="no-shrink column">
    <label class="mt-4 grey--text text--darken-1">Access requests:</label>
    <v-data-table
        :headers="tableHeaders"
        :items="project.access_requests"
        no-data-text="No access requests"
        hide-default-header
        :hide-default-footer="project.access_requests.length <= 10"
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
            <v-tooltip top v-if="item.user.profile && (item.user.profile.first_name || item.user.profile.last_name)">
              <template v-slot:activator="{ on }">
              <b v-on="on">
                {{ item.user.username }}
              </b>
              </template>
              <span>
              <span v-if="item.user.profile && item.user.profile.first_name">{{ item.user.profile.first_name }}</span>
              <span v-if="item.user.profile && item.user.profile.last_name"> {{ item.user.profile.last_name }}</span>
            </span>
            </v-tooltip>
            <b v-else>
              {{ item.user.username }}
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
            <v-select
              :items="['read', 'write', 'owner']"
              v-model="permissions[item.id]"
              return-object
              >
            </v-select>
          </td>
          <td class="justify-center px-0">
            <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  :disabled="expired(item.expire) || (project.creator === item.user.id || !project.access.owners.includes(app.user.id))"
                  @click="acceptRequest(item)"
                  elevation="0"
                  color="green"
                  class="white--text"
                >
                  accept
                </v-chip>
              </span>
            </template>
              <span>Accept request</span>
            </v-tooltip>
          </td>
          <td class="justify-center ">
            <v-tooltip bottom>
              <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  :disabled="project.creator === item.user.id || !project.access.owners.includes(app.user.id)"
                  @click="cancelRequest(item)"
                  elevation="0"
                  color="red"
                  class="white--text"
                >
                  cancel
                </v-chip>
              </span>
              </template>
              <span>Cancel access request</span>
            </v-tooltip>
          </td>
        </tr>
      </template>
    </v-data-table>
    <button ref="hidden-btn" id="accept-request-access-btn" style="visibility: hidden"/>
  </v-layout>
</template>

<script>
import { mapState } from 'vuex'
import MerginAPIMixin from '../mixins/MerginAPI'
import { postRetryCond } from '../http'

export default {
  mixins: [MerginAPIMixin],
  data () {
    return {
      permissions: {},
      tableHeaders: [
        {
          text: 'User',
          align: 'left',
          sortable: false,
          tooltip: 'Request from user'
        }, {
          text: 'Expire',
          align: 'left',
          sortable: false,
          tooltip: 'Project access request expiration date'
        }, {
          text: 'Permissions',
          align: 'right',
          sortable: false,
          width: 60
        }, {
          text: ' ',
          align: 'right',
          sortable: false,
          width: 60
        }, {
          text: '',
          align: 'right',
          sortable: false,
          width: 60
        }
      ],
      originalValue: null
    }
  },
  computed: {
    ...mapState(['project', 'app'])
  },
  created () {
    this.project.access_requests.forEach(request => {
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
          this.fetchProject(function () {})
        })
    },
    fetchProject () {
      this.$http(`/v1/project/${this.project.namespace}/${this.project.name}`)
        .then(resp => {
          this.$store.commit('project', resp.data)
        })
        .catch(resp => {
          this.$notification.error('Failed to load project data')
        })
    },
    expired (expire) {
      return Date.parse(expire) < Date.now()
    },
    cancelRequest (request) {
      this.cancelProjectAccessRequest(request)
      const accessRequests = [...this.project.access_requests]
      const index = this.project.access_requests.indexOf(request)
      if (index > -1) {
        accessRequests.splice(index, 1)
        this.project.access_requests = accessRequests
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
