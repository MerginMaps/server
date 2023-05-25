<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <!--    TODO: VUE 3 - cache-items prop has been removed, caching should be handled externally. -->
  <v-autocomplete
    ref="autocomplete"
    placeholder="Find user"
    v-model="users"
    :loading="isLoading"
    :items="items"
    :search-input.sync="query"
    cache-items
    multiple
    clearable
    hide-selected
    :filter="filterSelected"
    item-title="email"
    item-value="email"
    :no-data-text="
      !query || query.length <= 2
        ? 'Type more letters'
        : allowInvite
        ? 'No matches found - Try using their emails instead'
        : 'No matches found'
    "
    :hide-no-data="!query"
    hide-details
    return-object
    data-cy="account-autocomplete-input"
    @update:model-value="$emit('update', users)"
  >
    <template v-slot:selection="data">
      <user-search-chip
        :item="data.item"
        v-bind="data.attrs"
        :model-value="data.selected"
        close
        @click="data.select"
        @click:close="removeItem(data.item)"
      />
    </template>
    <template v-slot:item="{ item }">
      <v-list-item
        style="padding-bottom: 6px; padding-top: 6px"
        data-cy="account-autocomplete-list"
      >
        <template #prepend>
          <send-icon
            v-if="allowInvite && item.isInvite"
            size="18"
            class="text-primary"
          />
          <user-icon v-else size="18" class="text-primary" />
        </template>
        <v-list-item-title
          v-if="allowInvite && item.isInvite"
          v-html="`Invite \&quot;${item.email}\&quot; to your workspace`"
        ></v-list-item-title>
        <v-list-item-title
          v-else-if="!allowInvite || !item.isInvite"
          v-html="
            `${emphasizeMatch(item.username, query)}${
              getUserProfileName(item)
                ? ` &bull; ${getUserProfileName(item)}`
                : ''
            }`
          "
        ></v-list-item-title>
        <v-list-item-subtitle
          v-if="!allowInvite || !item.isInvite"
          v-html="emphasizeMatch(item.email, query)"
        ></v-list-item-subtitle>
      </v-list-item>
    </template>
    <template v-slot:append-item>
      <div class="text-right text-caption text-grey-darken-1">
        <span class="pr-1" v-if="items && items.some((item) => !item.isInvite)"
          >Not the right person? Try typing their email address instead!</span
        >
      </div>
    </template>
  </v-autocomplete>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import isEmpty from 'lodash/isEmpty'
import { mapState } from 'pinia'
import { defineComponent } from 'vue'
import { SendIcon, UserIcon } from 'vue-tabler-icons'

import { isValidEmail } from '@/common/text_utils'
import { useProjectStore } from '@/modules/project/store'
import UserSearchChip from '@/modules/user/components/UserSearchChip.vue'
import { EMPTY_INVITE_ITEM } from '@/modules/user/constants'
import { UserSearchParams } from '@/modules/user/types'
import { UserApi } from '@/modules/user/userApi'

export default defineComponent({
  name: 'AccountAutocomplete',
  components: { UserSearchChip, SendIcon, UserIcon },
  props: {
    inputUsers: Array,
    filterUsers: { type: Array, default: () => [] },
    allowInvite: Boolean
  },
  data() {
    return {
      searchResults: [],
      isLoading: false,
      query: '',
      users: []
    }
  },
  computed: {
    ...mapState(useProjectStore, ['currentNamespace']),
    items() {
      return this.searchResults.map((item) => {
        return { ...item }
      })
    }
  },
  created() {
    this.users = this.inputUsers ?? []
    this.refreshCachedItems(this.users)
  },
  watch: {
    query: 'search',
    inputUsers: {
      deep: true,
      handler(val) {
        this.users = val
        this.refreshCachedItems(val)
        if (!val || val.length === 0) {
          this.searchResults = []
          this.query = ''
        }
      }
    },
    users: {
      deep: true,
      handler(val) {
        this.$emit('update', val)
        if (!isEmpty(val)) {
          this.query = ''
        }
      }
    }
  },
  methods: {
    search: debounce(function () {
      // clear non-relevant cached items
      this.refreshCachedItems(this.users)

      if (!this.query || this.query.length < 3) {
        this.searchResults = []
        return
      }

      // Items have already been requested
      if (this.isLoading) {
        return
      }

      this.isLoading = true
      const params: UserSearchParams = {
        namespace: this.currentNamespace,
        like: this.query
      }
      UserApi.getAuthUserSearch(params)
        .then((resp) => {
          if (resp.data?.length > 0) {
            // return data from api in search results and remove items included in filterUsers
            this.searchResults = resp.data.filter(
              (item) => !this.filterUsers.find((user) => user === item.username)
            )
          } else if (this.allowInvite && isValidEmail(this.query)) {
            // return invite item in search results
            this.searchResults = [{ ...EMPTY_INVITE_ITEM, email: this.query }]
          } else {
            // return empty search results
            this.searchResults = []
          }
        })
        .finally(() => {
          this.isLoading = false
        })
    }, 300),

    filterSelected(item, queryText) {
      return (
        (item.username &&
          item.username
            .toLocaleLowerCase()
            .indexOf(queryText.toLocaleLowerCase()) > -1) ||
        (item.email &&
          item.email
            .toLocaleLowerCase()
            .indexOf(queryText.toLocaleLowerCase()) > -1)
      )
    },
    removeItem(item) {
      const index = this.users.findIndex((user) => item.email === user.email)
      if (index >= 0) {
        this.users.splice(index, 1)
      }
    },
    getUserProfileName(user) {
      const firstName = user?.profile?.first_name ?? ''
      const lastName = user?.profile?.last_name ?? ''
      return firstName || lastName ? `(${firstName} ${lastName})` : ''
    },
    emphasizeMatch(text, reg) {
      return text
        ? text.replace(new RegExp(reg, 'i'), function (str) {
            return '<b>' + str + '</b>'
          })
        : ''
    },
    refreshCachedItems(users) {
      if (this.$refs?.autocomplete) {
        // remove invalid values from cache
        this.$refs.autocomplete.cachedItems =
          this.$refs.autocomplete.cachedItems.filter(
            (cachedItem) =>
              users.findIndex(
                (user) =>
                  (this.allowInvite &&
                    user.isInvite &&
                    user.email === cachedItem.email) ||
                  (!user.isInvite && user.id === cachedItem.id)
              ) !== -1
          )
        // add missing values to cache
        users?.forEach((user) => {
          const idx = this.$refs.autocomplete.cachedItems.findIndex(
            (cachedItem) =>
              (this.allowInvite &&
                user.isInvite &&
                user.email === cachedItem.email) ||
              (!user.isInvite && user.id === cachedItem.id)
          )
          if (idx === -1) {
            this.$refs.autocomplete.cachedItems.push(user)
          }
        })
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.v-text-field .v-input__append-inner .v-input__icon--append {
  // hide append icon
  display: none;
}
.v-list {
  padding: 0;
}
</style>
