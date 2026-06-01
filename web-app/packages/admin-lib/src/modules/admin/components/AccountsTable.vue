<template>
  <div>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">
            Accounts
            <span class="text-color-medium-green">({{ users.count }})</span>
          </h1>
        </template>
        <template #headerActions>
          <PButton
            icon="ti ti-users-plus"
            @click="createUserDialog"
            label="Add user"
          />
        </template>
      </app-section>
    </app-container>
    <app-container>
      <app-section ground>
        <span class="p-input-icon-left w-full">
          <i class="ti ti-search paragraph-p3"></i>
          <PInputText
            placeholder="Search accounts"
            data-cy="search-members-field"
            v-model="search"
            class="w-full"
            @input="onSearch"
          />
        </span>
      </app-section>
    </app-container>
    <app-container>
      <app-section>
        <PDataTable
          :value="users.items"
          :lazy="true"
          :paginator="true"
          :rows="options.itemsPerPage"
          :rowsPerPageOptions="options.perPageOptions"
          :totalRecords="users.count"
          :loading="loading"
          :first="(options.page - 1) * options.itemsPerPage"
          :sort-field="options.sortBy[0]"
          :sort-order="options.sortDesc[0] ? -1 : 1"
          :rowHover="true"
          removableSort
          reorderable-columns
          @page="onPage"
          @sort="onSort"
          data-cy="accounts-table"
        >
          <template v-for="header in headers" :key="header.field">
            <PColumn
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="{ data }">
                <router-link
                  :to="accountRoute(data)"
                  class="dt-row-link"
                  :class="header.class"
                >
                  <template v-if="header.field === 'active'">{{
                    fieldValue(data, header.field) ? 'Active' : 'Inactive'
                  }}</template>
                  <template v-else>{{
                    fieldValue(data, header.field)
                  }}</template>
                </router-link>
              </template>
            </PColumn>
          </template>
          <template #paginatorstart>
            <PButton
              icon="ti ti-refresh"
              plain
              text
              rounded
              @click="onRefresh"
            />
          </template>
          <template #paginatorend />
        </PDataTable>
      </app-section>
    </app-container>
  </div>
</template>

<script lang="ts">
import {
  PaginatedUsersParams,
  TableDataHeader,
  useDataTableSearch,
  useDialogStore,
  AppContainer,
  AppSection
} from '@mergin/lib'
import get from 'lodash/get'
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { AdminRoutes } from '@/modules'
import CreateUserForm from '@/modules/admin/components/CreateUserForm.vue'
import { useAdminStore } from '@/modules/admin/store'

const headers: TableDataHeader[] = [
  {
    field: 'username',
    header: 'Username',
    sortable: true,
    linked: true,
    class: 'title-t4'
  },
  { field: 'email', header: 'Email', sortable: true, linked: true },
  { field: 'profile.name', header: 'Full name', linked: true },
  { field: 'active', header: 'Active', linked: true }
]

export default defineComponent({
  name: 'AccountsTable',
  components: {
    AppContainer,
    AppSection
  },
  setup() {
    const adminStore = useAdminStore()
    const dialogStore = useDialogStore()

    const tableSearch = useDataTableSearch({
      defaultSortBy: 'username',
      defaultSortDesc: false
    })

    tableSearch.setFetchFn((signal) => {
      const { options, search } = tableSearch
      const params: PaginatedUsersParams = {
        page: options.page,
        per_page: options.itemsPerPage
      }
      if (options.sortBy[0]) {
        params.descending = options.sortDesc[0]
        params.order_by = options.sortBy[0]
      }
      if (search.value) params.like = search.value.trim()
      adminStore.fetchUsers({ params, signal })
    })

    return {
      ...tableSearch,
      show: dialogStore.show.bind(dialogStore),
      headers
    }
  },
  computed: {
    ...mapState(useAdminStore, ['users', 'loading'])
  },
  created() {
    this.initFromQuery()
    this.doFetch()
  },
  methods: {
    fieldValue(data: unknown, field: string) {
      return get(data, field)
    },

    accountRoute(data) {
      return { name: AdminRoutes.ACCOUNT, params: { username: data.username } }
    },

    createUserDialog() {
      const dialog = { maxWidth: 500, header: 'Create user' }
      const listeners = {
        success: () => {
          this.options.page = 1
          this.doFetch()
        }
      }
      this.show({
        component: CreateUserForm,
        params: {
          listeners,
          dialog
        }
      })
    }
  }
})
</script>
