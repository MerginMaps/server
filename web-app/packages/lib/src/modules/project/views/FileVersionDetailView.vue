<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <v-list lines="two" subheader v-if="tables">
      <v-list-item v-bind:key="name" v-for="(value, name) in tables">
        <!--            TODO: VUE 3 - remove v-list-item-content -->
        <v-list-item-content>
          <v-list-item-title>
            <h3 class="text-primary">{{ name }}</h3>
          </v-list-item-title>
          <br />
          <v-data-table
            :headers="value.headers"
            :items="value.changes"
            no-data-text="No changeset"
            color="primary"
            footer-props.items-per-page-options='[10, 25, {"text": "$vuetify.dataIterator.rowsPerPageAll","value": -1}]'
            :hide-default-footer="value.changes.length <= 10"
            disable-sort
            style="overflow-x: auto"
          >
            <template #item.operationTypeHeader="{ value }">
              <v-icon size="small" :color="actions[value].color">{{
                actions[value].icon
              }}</v-icon>
            </template>
          </v-data-table>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <v-card v-else-if="!tables && !loading" class="mt-3" variant="tonal">
      <v-card-title><h4>Changes cannot be calculated</h4></v-card-title>
      <v-card-text
        >For details please check the
        <a :href="docsLinkManageSynchronisation" target="_blank"
          >documentation</a
        >.</v-card-text
      >
    </v-card>
  </div>
</template>

<script lang="ts">
import groupBy from 'lodash/groupBy'
import isArray from 'lodash/isArray'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { waitCursor } from '@/common/html_utils'
import { useNotificationStore } from '@/modules'
import { useInstanceStore } from '@/modules/instance/store'

export default defineComponent({
  name: 'FileVersionDetailView',
  props: {
    namespace: String,
    projectName: String,
    version_id: String,
    path: String,
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      tables: null,
      loading: true,
      actions: {
        insert: { icon: 'add_circle', color: 'green' },
        update: { icon: 'edit', color: 'orange' },
        delete: { icon: 'delete', color: 'red' }
      }
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    docsLinkManageSynchronisation() {
      return `${this.configData?.docs_url ?? ''}/manage/synchronisation`
    }
  },
  created() {
    this.getChangeset()
  },

  methods: {
    ...mapActions(useNotificationStore, ['error']),

    // TODO: refactor to pinia action
    getChangeset() {
      waitCursor(true)
      this.$http
        .get(
          `/v1/resource/changesets/${this.namespace}/${this.projectName}/${this.version_id}?path=${this.path}`
        )
        .then((resp) => {
          if (!resp.data.length) return
          // process data grouped by tables
          this.tables = {}
          let changeset = { ...resp.data }
          changeset = groupBy(changeset, 'table')
          // eslint-disable-next-line @typescript-eslint/no-this-alias
          const _this = this
          for (const [key, value] of Object.entries(changeset)) {
            _this.tables[key] = {}
            const headers = [
              { text: 'Change', value: 'operationTypeHeader', width: 50 }
            ]
            const changes = []
            if (isArray(value)) {
              const arrayValue = value as []
              arrayValue.forEach((data: any) => {
                if (data.table === 'gpkg_contents') {
                  return
                }
                data.values = { operationTypeHeader: data.type }
                data.changes.forEach((row) => {
                  const columnIdentifier = row.name
                  // based on operation type create a value to display: old, new or change old -> new
                  // display undefined values as N/A
                  row.value = {}
                  if (data.type === 'insert') {
                    data.values[columnIdentifier] =
                      typeof row.new === 'undefined' ? 'N/A' : row.new
                  } else if (data.type === 'update') {
                    if (typeof row.new === 'undefined') {
                      data.values[columnIdentifier] =
                        typeof row.old === 'undefined' ? 'N/A' : row.old
                    } else {
                      data.values[columnIdentifier] =
                        (typeof row.old === 'undefined' ? 'N/A' : row.old) +
                        ' ' +
                        String.fromCharCode(parseInt('2794', 16)) +
                        ' ' +
                        (typeof row.new === 'undefined' ? 'N/A' : row.new)
                    }
                  } else if (data.type === 'delete') {
                    data.values[columnIdentifier] =
                      typeof row.old === 'undefined' ? 'N/A' : row.old
                  }

                  if (!headers.map((h) => h.value).includes(columnIdentifier)) {
                    headers.push({
                      text: row.name,
                      value: columnIdentifier,
                      width: 50
                    })
                  }
                })
                changes.push(data.values)
              })
            }

            _this.tables[key].headers = headers
            _this.tables[key].changes = changes
          }
        })
        .catch((err) => {
          const msg = err.response
            ? err.response.data?.detail
            : 'Failed to display changeset of file'
          this.error({ text: msg })
        })
        .finally(() => {
          this.loading = false
          waitCursor(false)
        })
    }
  }
})
</script>
<style lang="scss" scoped>
:deep(.v-data-table__wrapper) {
  td.text-start {
    max-width: 250px;
  }
}
</style>
