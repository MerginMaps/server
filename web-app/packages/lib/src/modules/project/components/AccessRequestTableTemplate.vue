<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PDataView
    :value="accessRequests"
    :lazy="true"
    :paginator="accessRequestsCount > 10"
    :loading="loading"
    :rows="options.itemsPerPage"
    :totalRecords="accessRequestsCount"
    :data-key="'id'"
    :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
    size="small"
    @page="onPage"
    :pt="{
      header: {
        class: 'px-4 py-2'
      }
    }"
  >
    <template #header>
      <h3 class="font-semibold text-xs text-color m-0">Access requests</h3>
    </template>
    <template #list="slotProps">
      <template v-for="item in slotProps.items" :key="item.id">
        <!-- Row -->
        <div
          class="flex flex-column lg:flex-row align-items-center justify-content-between px-4 py-2 mt-0 border-bottom-1 border-gray-200"
        >
          <p class="w-12 lg:w-4 text-xs p-2 lg:p-0">
            User
            <span class="font-semibold">{{ item.requested_by }}</span>
            wants to transfer project
            <span class="font-semibold">{{ item.project_name }}</span>
            to your workspace.
          </p>
          <div
            class="flex w-12 lg:w-4 align-items-center flex-wrap lg:flex-nowrap"
          >
            <p
              v-tooltip.top="{ value: $filters.datetime(item.expire) }"
              class="opacity-80 text-xs w-12 lg:w-4 p-2 lg:p-1"
            >
              Expiring in {{ $filters.remainingtime(item.expire) }}
            </p>
            <AppDropdown
              v-if="showAccept"
              :options="[
                { value: 'read', label: 'Reader' },
                { value: 'write', label: 'Writer' },
                { value: 'owner', label: 'Owner' }
              ]"
              option-label="label"
              option-value="value"
              v-model="permissions[item.id]"
              @change="(e) => permissionsChange(e, item)"
              :disabled="expired(item.expire)"
              class="w-6 lg:w-4 p-1"
            />
            <div class="flex justify-content-end w-6 lg:w-4 p-1">
              <PButton
                icon="ti ti-x"
                rounded
                aria-label="Disallow"
                severity="danger"
                class="mr-2"
                @click="cancelRequest(item)"
              />
              <PButton
                v-if="showAccept"
                icon="ti ti-check"
                rounded
                aria-label="Accept"
                severity="success"
                :disabled="expired(item.expire)"
                @click="acceptRequest(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </template>
    <template #empty>
      <p>No access requests found</p>
    </template>
  </PDataView>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { DataViewPageEvent } from 'primevue/dataview'
import { DropdownChangeEvent } from 'primevue/dropdown'
import { defineComponent } from 'vue'

import AppDropdown from '@/common/components/AppDropdown.vue'
import { ProjectPermissionName } from '@/common/permission_utils'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import {
  GetAccessRequestsPayload,
  AccessRequest
} from '@/modules/project/types'

export default defineComponent({
  name: 'AccessRequestTableTemplate',
  components: { AppDropdown },
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
        sortBy: 'expire',
        sortDesc: false,
        itemsPerPage: 10,
        page: 1
      },
      selectedPermissions: {}
    }
  },
  computed: {
    ...mapState(useProjectStore, ['accessRequests', 'accessRequestsCount']),
    showAccept() {
      return this.namespace != null
    },
    ptColumn() {
      return {
        headerCell: {
          style: {
            backgroundColor: '#F8F9FA'
          }
        },
        headerTitle: {
          class: 'text-xs'
        }
      }
    },
    permissions(): Record<number, ProjectPermissionName> {
      return {
        ...this.accessRequests.reduce(
          (acc, curr) => ({
            ...acc,
            [curr.id]: 'read'
          }),
          {}
        ),
        ...this.selectedPermissions
      }
    }
  },
  methods: {
    ...mapActions(useProjectStore, [
      'cancelProjectAccessRequest',
      'acceptProjectAccessRequest',
      'getAccessRequests'
    ]),
    ...mapActions(useNotificationStore, ['error']),

    onPage(e: DataViewPageEvent) {
      this.options.page = e.page + 1
      this.options.itemsPerPage = e.rows
      this.fetchItems()
    },
    permissionsChange(e: DropdownChangeEvent, item: AccessRequest) {
      const { value } = e
      const { id } = item
      this.selectedPermissions[id] = value
    },
    /** Update pagination in case of last accepting / canceling feature */
    async updatePaginationOrFetch() {
      if (this.accessRequests.length === 1 && this.options.page > 1) {
        this.options.page -= 1
      }
      await this.fetchItems()
    },
    async acceptRequest(request) {
      try {
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
        const payload: GetAccessRequestsPayload = {
          namespace: this.namespace,
          params: {
            page: this.options.page,
            per_page: this.options.itemsPerPage,
            order_params:
              this.options.sortBy &&
              `${this.options.sortBy} ${this.options.sortDesc ? 'DESC' : 'ASC'}`
          }
        }
        await this.getAccessRequests(payload)
      } finally {
        this.loading = false
      }
    }
  }
})
</script>

<style lang="scss" scoped></style>
