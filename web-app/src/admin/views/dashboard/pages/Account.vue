# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <v-card color="transparent" outlined style="margin: 10px">
      <v-card-text>
        <v-layout row style="padding: 5px">
          <v-radio-group
          v-model="type"
          row
          style="max-width: 500px; padding-left: 10px"
          @change="resetPaging"
          >
            <v-radio
              label="User"
              value="user"
            ></v-radio>
            <v-radio
              label="Organisation"
              value="organisation"
            ></v-radio>
          </v-radio-group>
          <v-spacer></v-spacer>
          <v-text-field
          :label="$t('search')"
          color="secondary"
          hide-details
          style="max-width: 250px; padding-right: 10px"
          v-model="searchByName"
          @input="resetPaging"
          >
            <template
              v-if="$vuetify.breakpoint.mdAndUp"
              v-slot:prepend-inner
            >
              <v-icon elevation="1">mdi-magnify
              </v-icon>
            </template>
            <template v-slot:append>
              <v-icon elevation="1" @click="resetSearch">cancel</v-icon>
            </template>
          </v-text-field>
        </v-layout>
      </v-card-text>
    </v-card>
    <v-data-table
      height="70vh"
      :headers="headers"
      :items="accounts.items"
      :loading="loading"
      :no-data-text="(error) ? error : 'No accounts'"
      color="primary"
      :hide-default-footer="true"
      :options="options"
      :server-items-length="accounts.count"
      v-on:update:options="paginate"
  >
      <template v-slot:top="{ pagination, options, updateOptions }">
        <v-data-footer
          :pagination="pagination"
          :options="options"
          show-current-page
          show-first-last-page
          :items-per-page-options="[5,10,50]"
          @update:options="updateOptions"
        />
      </template>
    <template v-slot:item.name="{ item }">
       <span>
        <router-link :to="item.type === 'user' ? { name: 'admin-profile', params: { username: item.name }} : { name: 'admin-organisation', params: { name: item.name }}">
          {{ item.name }}
        </router-link>
       </span>
     </template>
    <template v-slot:item.storage="{ item }">
      {{  item.storage  | filesize("", 0) }}
    </template>
    <template v-slot:item.received="{ item }">
       <span>
         <v-tooltip bottom>
        <template v-slot:activator="{ on }">
        <span v-on="on">{{ item.received | timediff }}</span>
        </template>
        <span>{{ item.received | datetime }}</span>
      </v-tooltip>
       </span>
     </template>
    <template v-slot:item.msg="{ item }">
       <span>
         <v-tooltip bottom>
        <template v-slot:activator="{ on }">
        <span v-on="on">{{ item.msg.substring(0, 9) }}</span>
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
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { removeAccents } from '@/util'
import debounce from 'debounce'


export default {
  name: 'Account',
  data () {
    return {
      options: {
        sortBy: ['name'],
        sortDesc: [false],
        itemsPerPage: 10,
        page: 1
      },
      headers: [
        { text: 'Name', value: 'name', filterable: true, sortable: true },
        { text: 'Storage', value: 'storage', filterable: true, sortable: false },
        { text: 'Active', value: 'active', filterable: false, sortable: false, width: 15 }
      ],
      type: 'user',
      searchByName: ''
    }
  },
  props: {
    account_id: {
      type: Number,
      default: null
    }
  },
  computed: {
    ...mapState({
      accounts: state => state.admin.accounts,
      error: state => state.admin.error,
      loading: state => state.admin.loading
    })
  },
  created () {
    this.resetPaging = debounce(this.resetPaging, 1000)
    if (this.account_id !== null) {
      this.fetchAccount(this.account_id)
    }
  },
  watch: {
    error () {
      if (this.error) this.$notification.error(`Failed to fetch accounts. \n Reason: ${this.error}`)
    }
  },
  methods: {
    resetPaging () {
      this.options.page = 1
      this.paginate(this.options)
    },
    resetSearch () {
      this.searchByName = ''
      this.resetPaging()
    },
    paginate (options) {
      this.options = options
      const params = {
        page: options.page,
        per_page: options.itemsPerPage
      }
      if (options.sortBy[0]) {
        params.descending = options.sortDesc[0]
        params.order_by = options.sortBy[0]
      }
      if (this.searchByName) {
        params.name = removeAccents(this.searchByName.trim())
      }
      this.$store.dispatch('admin/fetchAccounts', { type: this.type, params: params })
    }
  }
}
</script>

<style scoped>

.theme--light.v-data-table, .theme--light.v-data-table .v-data-footer {
  border: none;
}

</style>
