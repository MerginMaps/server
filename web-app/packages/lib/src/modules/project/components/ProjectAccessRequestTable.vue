<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-data-table
      :headers="header"
      :items="accessRequestsData"
      ref="table"
      no-data-text="No access requests"
      color="primary"
      :footer-props="{ 'items-per-page-options': [10, 25, 50] }"
      :hide-default-footer="accessRequestsData.length <= 10"
      :options="options"
    >
      <template #item.expire="{ value }">
        <v-tooltip bottom>
          <template v-slot:activator="{ on }">
            <span v-on="on">{{ $filters.remainingtime(value) }}</span>
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
import { defineComponent } from 'vue'
import { mapActions, mapState } from 'vuex'

export default defineComponent({
  name: 'ProjectAccessRequestTable',
  props: {
    namespace: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      options: {
        'sort-by': 'name'
      },
      projectAccessRequests: [],
      permissions: {}
    }
  },
  computed: {
    ...mapState(['transfers']),
    ...mapState('projectModule', ['accessRequests', 'namespaceAccessRequests']),
    accessRequestsData() {
      return this.namespace == null
        ? this.accessRequests
        : this.namespaceAccessRequests
    },
    showAccept() {
      return this.namespace != null
    },
    header() {
      return [
        ...(this.namespace == null
          ? []
          : [{ text: 'Requester', value: 'requested_by', sortable: true }]),
        { text: 'Project name', value: 'project_name', sortable: true },
        { text: 'Expire in', value: 'expire', sortable: true },
        {
          text: 'Permissions',
          value: 'permission',
          width: 120,
          sortable: false
        },
        { text: '', value: 'buttons', width: 190, sortable: false }
      ]
    }
  },
  async created() {
    await this.reloadProjectAccessRequests({
      refetchGlobalAccessRequests: true,
      namespace: this.namespace
    })
    this.accessRequestsData.forEach((request) => {
      this.permissions[request.id] = 'read'
    })
  },
  methods: {
    ...mapActions('projectModule', [
      'cancelProjectAccessRequest',
      'acceptProjectAccessRequest',
      'reloadProjectAccessRequests'
    ]),

    async acceptRequest(request) {
      const el = this.$refs['hidden-btn']
      el.value = this.permissions[request.id]
      el.dispatchEvent(new Event('click', {}))

      const data = {
        permissions: this.permissions[request.id]
      }
      await this.acceptProjectAccessRequest({
        data,
        itemId: request.id,
        refetchGlobalAccessRequests: true,
        namespace: this.namespace
      })
    },
    changeSort(column) {
      if (this.options.sortBy === column) {
        this.options.descending = !this.options.descending
      } else {
        this.options.sortBy = column
        this.options.descending = false
      }
    },
    expired(expire) {
      return Date.parse(expire) < Date.now()
    },
    async cancelRequest(request) {
      await this.cancelProjectAccessRequest({
        itemId: request.id,
        refetchGlobalAccessRequests: true,
        namespace: this.namespace
      })
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

    :deep(.v-chip__content) {
      cursor: pointer;
      padding: 0 0.5em;
      font-size: 85%;
    }
  }
}
</style>
