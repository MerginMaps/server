# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card v-on:keyup.enter="requestTransfer">
    <v-card-title>
      <span class="headline">Transfer project</span>
      <span class="transfer-zone-warning">
        It will move all files into new namespace once new owner accepts the request. You may lose access to it.
      </span>
    </v-card-title>
    <v-card-text>
      <v-text-field
        disabled
        label="project"
        v-model="project"
        :error-messages="errors.project"
      />
      <v-text-field
        disabled
        label="original owner"
        v-model="from_namespace"
        :error-messages="errors.from_namespace"
      />
      <v-radio-group
          v-model="type"
          row
          style="max-width: 500px; padding-left: 10px"
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
     <v-autocomplete
        placeholder="target owner"
        v-model="to_namespace"
        :loading="isLoading"
        :items="searchResults"
        :search-input.sync="query"
        clearable
        return-object
        no-data-text="Type more letters"
        :hide-no-data="query && query.length > 2"
        hide-details
      >
        <template slot="item" slot-scope="{ item }">
          <v-list-item-content>
            <div class="v-list-item-content">
              <b>{{ item.text }} </b>
            </div>
          </v-list-item-content>
        </template>
      </v-autocomplete>
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn @click="$dialog.close">
        Close
      </v-btn>
      <v-btn
        class="primary"
        :disabled="!project || !from_namespace || !to_namespace"
        @click="requestTransfer"
      >
        Request transfer
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import debounce from 'lodash/debounce'
import FormMixin from '@/mixins/Form'
import { waitCursor } from '../util'
import { postRetryCond } from '../http'

export default {
  mixins: [FormMixin],
  props: {
    project: String,
    from_namespace: String
  },
  data () {
    return {
      to_namespace: '',
      // search data
      isLoading: false,
      query: '',
      searchResults: [],
      type: 'user'
    }
  },
  watch: {
    query: 'search'
  },
  methods: {
    requestTransfer () {
      this.clearErrors()
      const data = {
        namespace: this.to_namespace.value
      }
      waitCursor(true)
      this.$http.post(`/v1/project/transfer/${this.from_namespace}/${this.project}`, data, { 'axios-retry': { retries: 5, retryCondition: error => postRetryCond(error) } })
        .then((resp) => {
          waitCursor(false)
          this.$dialog.close()
          this.$emit('submit')
        })
        .catch(err => {
          waitCursor(false)
          this.$dialog.close()
          const msg = (err.response) ? err.response.data.detail : 'Failed to create project transfer'
          this.$notification.error(msg)
        })
    },

    search: debounce(function () {
      if (this.namespace && this.query === this.namespace.text) {
        return
      }
      if (!this.query || this.query.length < 3) {
        this.searchResults = []
        return
      }
      this.isLoading = true
      const params = { q: this.query }
      this.$http.get(`/v1/namespaces/${this.type}`, { params })
        .then(resp => {
          this.searchResults = resp.data
            .filter(u => u.name !== this.from_namespace)
            .map(u => ({
              value: u.name,
              text: u.name,
              fullText: `${u.name} (${u.type})`
            }))
          this.isLoading = false
        })
        .catch(() => {
          this.isLoading = false
        })
    }, 300)
  }
}
</script>
<style lang="scss" scoped>
  .transfer-zone-warning{
    color: red;
    margin-top: 10px;
    display: block;
    font-size: 14px;
  }
  .v-card__title{
    word-break: normal;
  }
  .headline{
    font-size: 24px !important;
  }
</style>
