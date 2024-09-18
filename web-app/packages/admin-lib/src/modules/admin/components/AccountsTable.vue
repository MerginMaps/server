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
            placeholder="Search members"
            data-cy="search-members-field"
            v-model="searchByName"
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
          removableSort
          reorderable-columns
          @page="onPage"
          @row-click="rowClick"
          @sort="onSort"
          data-cy="accounts-table"
        >
          <template v-for="header in headers" :key="header.field">
            <PColumn
              v-if="header.field === 'username'"
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            >
              <template #body="slotProps">
                <router-link
                  class="title-t4"
                  :to="{
                    name: 'account',
                    params: { username: slotProps.data.username }
                  }"
                >
                  {{ slotProps.data.username }}
                </router-link>
              </template>
            </PColumn>
            <PColumn
              v-else-if="header.field === 'active'"
              :header="header.header"
              :field="header.field"
            >
              <template #body="slotProps">
                <i v-if="slotProps.data.active" class="ti ti-check" />
                <i v-else class="ti ti-x" />
              </template>
            </PColumn>
            <PColumn
              v-else
              :field="header.field"
              :header="header.header"
              :sortable="header.sortable"
            ></PColumn>
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
  useDialogStore,
  TableDataHeader,
  AppContainer,
  AppSection
} from '@mergin/lib'
import debounce from 'lodash/debounce'
import { mapActions, mapState } from 'pinia'
import {
  DataTablePageEvent,
  DataTableRowClickEvent,
  DataTableSortEvent
} from 'primevue/datatable'
import { defineComponent } from 'vue'

import { AdminRoutes } from '@/modules'
import CreateUserForm from '@/modules/admin/components/CreateUserForm.vue'
import { useAdminStore } from '@/modules/admin/store'

export default defineComponent({
  name: 'AccountsTable',
  components: {
    AppContainer,
    AppSection
  },
  data() {
    return {
      options: {
        sortBy: ['username'],
        sortDesc: [false],
        itemsPerPage: 20,
        page: 1,
        perPageOptions: [20, 50, 100]
      },
      searchByName: '',
      headers: [
        { field: 'username', header: 'Name', sortable: true },
        { field: 'email', header: 'Email', sortable: true },
        { field: 'profile.name', header: 'Username' },
        { field: 'active', header: 'Active' }
      ] as TableDataHeader[]
    }
  },
  computed: {
    ...mapState(useAdminStore, ['users', 'loading'])
  },
  created() {
    this.resetPaging = debounce(this.resetPaging, 1000)
    this.fetchUsers({ params: this.getParams() })
  },
  methods: {
    ...mapActions(useAdminStore, ['fetchUsers']),
    ...mapActions(useDialogStore, ['show']),

    onSearch() {
      this.resetPaging()
      this.fetchUsers({ params: this.getParams() })
    },

    async resetPaging() {
      this.options.page = 1
    },

    getParams(): PaginatedUsersParams {
      const params = {
        page: this.options.page,
        per_page: this.options.itemsPerPage
      } as PaginatedUsersParams
      if (this.options.sortBy[0]) {
        params.descending = this.options.sortDesc[0]
        params.order_by = this.options.sortBy[0]
      }
      if (this.searchByName) {
        params.like = this.searchByName.trim()
      }
      return params
    },

    onRefresh() {
      this.fetchUsers({ params: this.getParams() })
    },

    onPage(event: DataTablePageEvent) {
      this.options.page = event.page + 1
      this.options.itemsPerPage = event.rows
      this.fetchUsers({ params: this.getParams() })
    },

    onSort(event: DataTableSortEvent) {
      this.options.sortBy[0] = event.sortField?.toString()
      this.options.sortDesc[0] = event.sortOrder < 1
      this.fetchUsers({ params: this.getParams() })
    },

    rowClick(event: DataTableRowClickEvent) {
      this.$router.push({
        name: AdminRoutes.ACCOUNT,
        params: { username: event.data.username }
      })
    },

    createUserDialog() {
      const dialog = { maxWidth: 500, header: 'Create user' }
      const listeners = {
        success: () => {
          this.resetPaging()
          this.fetchUsers({ params: this.getParams() })
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
