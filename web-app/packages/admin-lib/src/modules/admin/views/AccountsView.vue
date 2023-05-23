<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <v-card color="transparent" variant="outlined" style="margin: 10px">
      <v-card-text>
        <v-layout row style="padding: 5px">
          <v-btn
            class="ma-1"
            color="primary"
            variant="outlined"
            rounded
            @click="createUserDialog"
          >
            <v-icon>mdi-account-plus</v-icon>
          </v-btn>
          <v-spacer></v-spacer>
          <v-text-field
            :label="$t('search')"
            color="secondary"
            hide-details
            style="max-width: 250px; padding-right: 10px"
            v-model="searchByName"
            @update:model-value="resetPaging"
          >
            <template v-if="$vuetify.display.mdAndUp" v-slot:prepend-inner>
              <v-icon elevation="1">mdi-magnify</v-icon>
            </template>
            <template v-slot:append-inner>
              <v-icon elevation="1" @click="resetSearch">cancel</v-icon>
            </template>
          </v-text-field>
        </v-layout>
      </v-card-text>
    </v-card>
    <v-data-table
      height="70vh"
      :headers="headers"
      :items="users.items"
      :loading="loading"
      no-data-text="No users"
      color="primary"
      :hide-default-footer="true"
      :options="options"
      :server-items-length="users.count"
      v-on:update:options="paginate"
    >
      <template v-slot:top="{ pagination, options, updateOptions }">
        <v-data-footer
          :pagination="pagination"
          :options="options"
          show-current-page
          show-first-last-page
          :items-per-page-options="[5, 10, 50]"
          @update:options="updateOptions"
        />
      </template>
      <template v-slot:item.username="{ item }">
        <span>
          <router-link
            :to="{ name: 'profile', params: { username: item.username } }"
          >
            {{ item.username }}
          </router-link>
        </span>
      </template>
      <template v-slot:item.received="{ item }">
        <span>
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <span v-bind="props">{{ $filters.timediff(item.received) }}</span>
            </template>
            <span>{{ $filters.datetime(item.received) }}</span>
          </v-tooltip>
        </span>
      </template>
      <template v-slot:item.msg="{ item }">
        <span>
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <span v-bind="props">{{ item.msg.substring(0, 9) }}</span>
            </template>
            <span>{{ item.msg }}</span>
          </v-tooltip>
        </span>
      </template>
      <template v-slot:item.active="{ item }">
        <span>
          <span style="display: inline-block; width: 120px">
            <v-icon v-if="item.active" color="green">check</v-icon>
            <v-icon v-else color="red">clear</v-icon>
          </span>
        </span>
      </template>
    </v-data-table>
  </admin-layout>
</template>

<script lang="ts">
import { PaginatedUsersParams, useDialogStore } from '@mergin/lib'
import debounce from 'lodash/debounce'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import CreateUserForm from '@/modules/admin/components/CreateUserForm.vue'
import { useAdminStore } from '@/modules/admin/store'

export default defineComponent({
  name: 'AccountView',
  components: {
    AdminLayout
  },
  data() {
    return {
      options: {
        sortBy: ['username'],
        sortDesc: [false],
        itemsPerPage: 10,
        page: 1
      },
      headers: [
        { text: 'Name', value: 'username', filterable: true, sortable: true },
        {
          text: 'Active',
          value: 'active',
          filterable: false,
          sortable: false,
          width: 15
        }
      ],
      searchByName: ''
    }
  },
  computed: {
    ...mapState(useAdminStore, ['users', 'loading'])
  },
  created() {
    this.resetPaging = debounce(this.resetPaging, 1000)
  },
  methods: {
    ...mapActions(useAdminStore, ['fetchUsers']),
    ...mapActions(useDialogStore, ['show']),

    async resetPaging() {
      this.options.page = 1
      await this.paginate(this.options)
    },

    async resetSearch() {
      this.searchByName = ''
      await this.resetPaging()
    },

    async paginate(options) {
      this.options = options
      const params = {
        page: options.page,
        per_page: options.itemsPerPage
      } as PaginatedUsersParams
      if (options.sortBy[0]) {
        params.descending = options.sortDesc[0]
        params.order_by = options.sortBy[0]
      }
      if (this.searchByName) {
        params.like = this.searchByName.trim()
      }
      await this.fetchUsers({ params })
    },

    createUserDialog() {
      const dialog = { maxWidth: 500, persistent: true }
      const listeners = {
        success: async () => this.resetPaging()
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

<style scoped>
.theme--light.v-data-table,
.theme--light.v-data-table .v-data-footer {
  border: none;
}
</style>
