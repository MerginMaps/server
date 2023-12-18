<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-layout class="no-shrink column">
    <label class="mt-4 text-grey-darken-1">Access requests:</label>
    <!-- <v-data-table
      :loading="loading"
      :headers="tableHeaders"
      :items="accessRequests"
      :server-items-length="accessRequestsCount"
      no-data-text="No access requests"
      :options="options"
      v-on:update:options="onUpdateOptions"
      :footer-props="{ 'items-per-page-options': [10, 25, 50] }"
    >
      <template #header.user="{ header }">
        <v-tooltip v-if="header.tooltip" location="top">
          <template v-slot:activator="{ props }">
            <span v-bind="props">
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
        <v-tooltip v-if="header.tooltip" location="top">
          <template v-slot:activator="{ props }">
            <span v-bind="props">
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
          <template v-slot:activator="{ props }">
            <b v-bind="props">
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
        <v-tooltip location="bottom">
          <template v-slot:activator="{ props }">
            <span v-bind="props">{{ $filters.remainingtime(value) }}</span>
          </template>
          <span>{{ $filters.datetime(value) }}</span>
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
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <span v-bind="props">
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
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <span v-bind="props">
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
    </v-data-table> -->
    <button
      ref="hidden-btn"
      id="accept-request-access-btn"
      style="visibility: hidden"
    />
  </v-layout>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { getErrorMessage } from '@/common/error_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { GetProjectAccessRequestsPayload } from '@/modules'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  data() {
    return {
      loading: false,
      options: {
        // Default is order_params=expire ASC
        sortBy: ['expire'],
        sortDesc: [false],
        itemsPerPage: 10,
        page: 1
      },
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
    ...mapState(useProjectStore, [
      'project',
      'accessRequests',
      'accessRequestsCount'
    ]),
    ...mapState(useUserStore, ['loggedUser'])
  },
  methods: {
    ...mapActions(useProjectStore, [
      'cancelProjectAccessRequest',
      'acceptProjectAccessRequest',
      'getProjectAccessRequests'
    ]),
    ...mapActions(useNotificationStore, ['error']),

    onUpdateOptions(options) {
      this.options = options
      this.fetchItems()
    },
    /** Update pagination in case of last accepting / canceling feature */
    async updatePaginationOrFetch() {
      if (this.accessRequests.length === 1 && this.options.page > 1) {
        this.options.page -= 1
        return
      }
      await this.fetchItems()
    },
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
          namespace: this.project.namespace
        })
        await this.updatePaginationOrFetch()
      } catch (err) {
        this.error({
          text: getErrorMessage(err, 'Failed to accept access request')
        })
      }
    },
    expired(expire) {
      return Date.parse(expire) < Date.now()
    },
    async cancelRequest(request) {
      await this.cancelProjectAccessRequest({
        itemId: request.id,
        namespace: this.project.namespace
      })
      await this.updatePaginationOrFetch()
    },
    async fetchItems() {
      this.loading = true
      try {
        const payload: GetProjectAccessRequestsPayload = {
          namespace: this.project.namespace,
          params: {
            page: this.options.page,
            per_page: this.options.itemsPerPage,
            order_params:
              this.options.sortBy[0] &&
              `${this.options.sortBy[0]} ${
                this.options.sortDesc[0] ? 'DESC' : 'ASC'
              }`,
            project_name: this.project.name
          }
        }
        await this.getProjectAccessRequests(payload)
        this.accessRequests.forEach((request) => {
          this.permissions[request.id] = 'read'
        })
      } finally {
        this.loading = false
      }
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

:deep(*) {
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

.div {
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
