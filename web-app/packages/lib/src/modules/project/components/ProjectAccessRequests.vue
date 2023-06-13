<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout class="no-shrink column">
    <label class="mt-4 grey--text text--darken-1">Access requests:</label>
    <v-data-table
      :headers="tableHeaders"
      :items="project.access_requests"
      no-data-text="No access requests"
      :hide-default-footer="project.access_requests.length <= 10"
    >
      <template #header.user="{ header }">
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
      </template>
      <template #header.expire="{ header }">
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
      </template>
      <template #item.user="{ value }">
        <v-tooltip
          top
          v-if="
            value.profile &&
            (value.profile.first_name || value.profile.last_name)
          "
        >
          <template v-slot:activator="{ on }">
            <b v-on="on">
              {{ value.username }}
            </b>
          </template>
          <span>
            <span v-if="value.profile && value.profile.first_name">{{
              value.profile.first_name
            }}</span>
            <span v-if="value.profile && value.profile.last_name">
              {{ value.profile.last_name }}</span
            >
          </span>
        </v-tooltip>
        <b v-else>
          {{ value.username }}
        </b>
      </template>
      <template #item.expire="{ value }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <span v-on="on">{{ value | remainingtime }}</span>
          </template>
          <span>{{ value | datetime }}</span>
        </v-tooltip>
      </template>
      <template #item.permissions="{ item }">
        <v-select
          :items="['read', 'write', 'owner']"
          v-model="permissions[item.id]"
          return-object
        >
        </v-select>
      </template>
      <template #item.confirm="{ item }">
        <div class="justify-center px-0">
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  :disabled="!canAcceptAccessRequest(item.user.id, item.expire)"
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
        </div>
      </template>
      <template #item.cancel="{ item }">
        <div class="justify-center">
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span v-on="on">
                <v-chip
                  :disabled="!canCancelAccessRequest(item.user.id)"
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
        </div>
      </template>
    </v-data-table>
    <button
      ref="hidden-btn"
      id="accept-request-access-btn"
      style="visibility: hidden"
    />
  </v-layout>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapActions, mapState } from 'vuex'

import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'

export default Vue.extend({
  data() {
    return {
      permissions: {},
      tableHeaders: [
        {
          text: 'User',
          value: 'user',
          align: 'left',
          sortable: false,
          tooltip: 'Request from user'
        },
        {
          text: 'Expire',
          value: 'expire',
          align: 'left',
          sortable: false,
          tooltip: 'Project access request expiration date'
        },
        {
          text: 'Permissions',
          value: 'permissions',
          align: 'right',
          sortable: false,
          width: 60
        },
        {
          text: ' ',
          value: 'confirm',
          align: 'right',
          sortable: false,
          width: 60
        },
        {
          text: '',
          value: 'cancel',
          align: 'right',
          sortable: false,
          width: 60
        }
      ],
      originalValue: null
    }
  },
  computed: {
    ...mapState('projectModule', ['project']),
    ...mapState('userModule', ['loggedUser'])
  },
  created() {
    this.project.access_requests.forEach((request) => {
      this.permissions[request.id] = 'read'
    })
  },
  methods: {
    ...mapActions('projectModule', [
      'cancelProjectAccessRequest',
      'acceptProjectAccessRequest',
      'fetchProject'
    ]),
    ...mapActions('notificationModule', ['error']),

    canAcceptAccessRequest(userId: number, expire: string) {
      return (
        !this.expired(expire) &&
        this.project.creator !== userId &&
        isAtLeastProjectRole(this.project.role, ProjectRole.owner)
      )
    },
    canCancelAccessRequest(userId: number) {
      return (
        this.project.creator !== userId &&
        isAtLeastProjectRole(this.project.role, ProjectRole.owner)
      )
    },
    async acceptRequest(request) {
      try {
        const el = this.$refs['hidden-btn']
        el.value = this.permissions[request.id]
        el.dispatchEvent(new Event('click', {}))
        const data = {
          permissions: this.permissions[request.id]
        }
        await this.acceptProjectAccessRequest({
          data,
          itemId: request.id,
          namespace: this.project.namespace,
          projectName: this.project.name
        })
        await this.fetchProject({
          namespace: this.project.namespace,
          projectName: this.project.name
        })
      } catch (err) {
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to accept access request'
        this.error({ text: msg })
      }
    },
    expired(expire) {
      return Date.parse(expire) < Date.now()
    },
    async cancelRequest(request) {
      await this.cancelProjectAccessRequest({
        itemId: request.id,
        namespace: this.project.namespace,
        projectName: this.project.name
      })
      await this.fetchProject({
        namespace: this.project.namespace,
        projectName: this.project.name
      })
    }
  }
})
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
