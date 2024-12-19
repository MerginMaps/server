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
  >
    <template #header>
      <h3 class="font-semibold paragraph-p6 text-color m-0">Access requests</h3>
    </template>
    <template #list="slotProps">
      <template v-for="item in slotProps.items" :key="item.id">
        <!-- Row -->
        <div
          class="flex flex-column lg:flex-row align-items-center justify-content-between px-4 py-2 mt-0 border-bottom-1 border-gray-200"
        >
          <p class="w-12 lg:w-6 paragraph-p6 m-0">
            User
            <span class="font-semibold">{{ item.requested_by }}</span>
            requested an access to your project
            <span class="font-semibold">{{ item.project_name }}.</span>
          </p>
          <div
            class="flex w-12 lg:w-4 align-items-center flex-wrap lg:flex-nowrap row-gap-2"
          >
            <p class="opacity-80 paragraph-p6 w-12">
              <span v-tooltip.right="{ value: $filters.datetime(item.expire) }">
                <template
                  v-if="$filters.remainingtime(item.expire) === 'expired'"
                  >Expired</template
                >
                <template v-else
                  >Expiring in
                  {{ $filters.remainingtime(item.expire) }}</template
                >
              </span>
            </p>
            <AppDropdown
              :options="availablePermissions"
              v-model="permissions[item.id]"
              class="w-6 lg:w-5 lg:mr-2"
            />
            <div class="flex justify-content-end w-6 lg:w-4">
              <PButton
                :disabled="!canCancelAccessRequest()"
                icon="ti ti-x"
                rounded
                aria-label="Disallow"
                severity="danger"
                class="mr-2"
                @click="cancelRequest(item)"
              />
              <PButton
                :disabled="!canAcceptAccessRequest(item.expire)"
                icon="ti ti-check"
                rounded
                aria-label="Accept"
                severity="success"
                @click="acceptRequest(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </template>
    <template #empty>
      <p class="text-center p-4 m-0">No access requests found</p>
    </template>
  </PDataView>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { DataViewPageEvent } from 'primevue/dataview'
import { defineComponent } from 'vue'

import AppDropdown from '@/common/components/AppDropdown.vue'
import { getErrorMessage } from '@/common/error_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { GetAccessRequestsPayload } from '@/modules'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
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
      permissions: {}
    }
  },
  components: { AppDropdown },
  computed: {
    ...mapState(useProjectStore, [
      'project',
      'accessRequests',
      'accessRequestsCount',
      'availablePermissions'
    ]),
    ...mapState(useUserStore, ['loggedUser'])
  },
  created() {
    this.fetchItems()
  },
  methods: {
    ...mapActions(useProjectStore, [
      'cancelProjectAccessRequest',
      'acceptProjectAccessRequest',
      'getAccessRequests'
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
    canAcceptAccessRequest(expire: string) {
      return (
        !this.expired(expire) &&
        isAtLeastProjectRole(this.project.role, ProjectRole.owner)
      )
    },
    canCancelAccessRequest() {
      return isAtLeastProjectRole(this.project.role, ProjectRole.owner)
    },
    async acceptRequest(request) {
      try {
        const data = {
          permissions: this.permissions[request.id]
        }
        await this.acceptProjectAccessRequest({
          data,
          itemId: request.id,
          workspace: this.project.namespace
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
        workspace: this.project.namespace
      })
      await this.updatePaginationOrFetch()
    },
    async fetchItems() {
      this.loading = true
      try {
        const payload: GetAccessRequestsPayload = {
          namespace: this.project.namespace,
          params: {
            project_name: this.project.name,
            page: this.options.page,
            per_page: this.options.itemsPerPage,
            order_params:
              this.options.sortBy[0] &&
              `${this.options.sortBy[0]} ${
                this.options.sortDesc[0] ? 'DESC' : 'ASC'
              }`
          }
        }
        await this.getAccessRequests(payload)
        this.accessRequests.forEach((request) => {
          this.permissions[request.id] = 'read'
        })
      } finally {
        this.loading = false
      }
    },
    onPage(e: DataViewPageEvent) {
      this.options.page = e.page + 1
      this.options.itemsPerPage = e.rows
      this.fetchItems()
    }
  }
})
</script>

<style lang="scss" scoped></style>
