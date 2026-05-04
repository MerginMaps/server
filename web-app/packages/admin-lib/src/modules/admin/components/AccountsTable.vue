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
        { field: 'username', header: 'Username', sortable: true },
        { field: 'email', header: 'Email', sortable: true },
        { field: 'profile.name', header: 'Full name' },
        { field: 'active', header: 'Active' }
      ] as TableDataHeader[],
      abortController: null as AbortController | null
    }
  },
  computed: {
    ...mapState(useAdminStore, ['users', 'loading'])
  },
  created() {
    // Restore any search/sort/page state from the URL before the first fetch
    this.initFromQuery()
    // Delay search-triggered fetches so rapid typing doesn't spam the API
    this.onSearch = debounce(this.onSearch, 500)
    this.doFetch()
  },
  methods: {
    ...mapActions(useAdminStore, ['fetchUsers']),
    ...mapActions(useDialogStore, ['show']),

    // Seed local state from URL query params so the page is shareable / survives navigation
    initFromQuery() {
      const q = this.$route.query
      if (q.q) this.searchByName = String(q.q)
      if (q.page) this.options.page = Number(q.page)
      if (q.per_page) this.options.itemsPerPage = Number(q.per_page)
      if (q.order_by) this.options.sortBy[0] = String(q.order_by)
      if (q.desc) this.options.sortDesc[0] = q.desc === 'true'
    },

    // Reflect current search/sort/page state into the URL (defaults are omitted to keep URLs clean)
    updateQuery() {
      const query: Record<string, string> = {}
      if (this.searchByName) query.q = this.searchByName
      if (this.options.page > 1) query.page = String(this.options.page)
      if (this.options.itemsPerPage !== 20)
        query.per_page = String(this.options.itemsPerPage)
      if (this.options.sortBy[0] && this.options.sortBy[0] !== 'username')
        query.order_by = this.options.sortBy[0]
      if (this.options.sortDesc[0]) query.desc = 'true'
      // replace (not push) so back-button skips intermediate search states
      this.$router.replace({ query })
    },

    // Single entry point for all fetches: cancels any in-flight request, syncs the URL, then fetches
    doFetch() {
      // Abort the previous request so a stale slower response can't overwrite a newer one
      this.abortController?.abort()
      this.abortController = new AbortController()
      this.updateQuery()
      this.fetchUsers({
        params: this.getParams(),
        signal: this.abortController.signal
      })
    },

    // Called on every keystroke (debounced); resets to page 1 so results start from the beginning
    onSearch() {
      this.options.page = 1
      this.doFetch()
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
      this.doFetch()
    },

    onPage(event: DataTablePageEvent) {
      this.options.page = event.page + 1
      this.options.itemsPerPage = event.rows
      this.doFetch()
    },

    onSort(event: DataTableSortEvent) {
      this.options.sortBy[0] = event.sortField?.toString()
      this.options.sortDesc[0] = event.sortOrder < 1
      this.doFetch()
    },

    rowClick(event: DataTableRowClickEvent) {
      const originalEvent = event.originalEvent as MouseEvent
      // Let the browser handle clicks that originate from a link inside the row (e.g. username column)
      if ((originalEvent.target as HTMLElement).closest('a')) return

      const location = {
        name: AdminRoutes.ACCOUNT,
        params: { username: event.data.username }
      }
      // Ctrl/Cmd/Shift+click opens in a new tab; plain click navigates in the same tab
      if (originalEvent.ctrlKey || originalEvent.metaKey || originalEvent.shiftKey) {
        window.open(this.$router.resolve(location).href, '_blank')
      } else {
        this.$router.push(location)
      }
    },

    createUserDialog() {
      const dialog = { maxWidth: 500, header: 'Create user' }
      const listeners = {
        success: () => {
          // After creating a user, go back to page 1 so the new account is visible
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
