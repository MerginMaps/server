<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-data-table
      :loading="loading"
      :items="accessRequests"
      :server-items-length="accessRequestsCount"
      :headers="headers"
      ref="table"
      no-data-text="No access requests"
      color="primary"
      :footer-props="{ 'items-per-page-options': [10, 25, 50] }"
      :hide-default-footer="accessRequestsCount <= 10"
      :options="options"
      v-on:update:options="onUpdateOptions"
    >
      <template #item.expire="{ value }">
        <v-tooltip location="bottom">
          <template v-slot:activator="{ props }">
            <span v-bind="props">{{ $filters.remainingtime(value) }}</span>
          </template>
          <span>{{ $filters.datetime(value) }}</span>
        </v-tooltip>
      </template>
      <template #item.permission="{ item }">
        <v-select
          :items="['read', 'write', 'owner']"
          v-model="permissions[item.id]"
          return-object
          :disabled="!showAccept"
        >
        </v-select>
      </template>
      <template #item.buttons="{ item }">
        <div class="justify-center">
          <div style="text-align: end">
            <v-tooltip bottom v-if="showAccept">
              <template v-slot:activator="{ props }">
                <span v-bind="props">
                  <v-chip
                    :disabled="expired(item.expire)"
                    @click="acceptRequest(item)"
                    elevation="0"
                    color="green"
                    class="white--text"
                    :value="permissions[item.id]"
                    :model-value="permissions[item.id]"
                  >
                    accept
                  </v-chip>
                </span>
              </template>
              <span>Accept request</span>
            </v-tooltip>
            <v-tooltip location="bottom">
              <template v-slot:activator="{ props }">
                <span v-bind="props">
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
        </div>
      </template>
    </v-data-table>
    <button
      ref="hidden-btn"
      id="accept-request-access-btn"
      style="visibility: hidden"
    />
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import {
  GetProjectAccessRequestsPayload,
  TableDataHeader
} from '@/modules/project/types'

export default defineComponent({
  name: 'ProjectAccessRequestTableTemplate',
  props: {
    namespace: {
      type: String,
      default: null
    }
  },
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
      permissions: {}
    }
  },
  computed: {
    ...mapState(useProjectStore, ['accessRequests', 'accessRequestsCount']),
    showAccept() {
      return this.namespace != null
    },
    headers() {
      let headers: TableDataHeader[] = [
        { text: 'Project name', value: 'project_name', sortable: true },
        { text: 'Expires in', value: 'expire', sortable: true }
      ]
      if (this.namespace) {
        headers = [
          { text: 'Requester', value: 'requested_by', sortable: true },
          ...headers,
          {
            text: 'Permissions',
            value: 'permission',
            width: 120,
            sortable: false
          }
        ]
      }
      return [
        ...headers,
        { text: '', value: 'buttons', width: 190, sortable: false }
      ]
    }
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
          namespace: this.namespace
        })
        await this.updatePaginationOrFetch()
      } catch (err) {
        this.$emit('accept-access-request-error', err)
      }
    },
    expired(expire) {
      return Date.parse(expire) < Date.now()
    },
    async cancelRequest(request) {
      await this.cancelProjectAccessRequest({
        itemId: request.id,
        namespace: this.namespace
      })
      await this.updatePaginationOrFetch()
    },
    async fetchItems() {
      this.loading = true
      try {
        const payload: GetProjectAccessRequestsPayload = {
          namespace: this.namespace,
          params: {
            page: this.options.page,
            per_page: this.options.itemsPerPage,
            order_params:
              this.options.sortBy[0] &&
              `${this.options.sortBy[0]} ${
                this.options.sortDesc[0] ? 'DESC' : 'ASC'
              }`
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

    :deep(*) .v-chip__content {
      cursor: pointer;
      padding: 0 0.5em;
      font-size: 85%;
    }
  }
}
</style>
