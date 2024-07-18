<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container v-if="loading && !tables">
      <PSkeleton width="4rem" height="2rem" class="mb-3"></PSkeleton>
      <PSkeleton width="100%" height="150px"></PSkeleton>
    </app-container>

    <template v-if="tables">
      <app-container>
        <app-section ground>
          <template #header
            ><h1 class="headline-h3">{{ path }}</h1></template
          >
        </app-section>
      </app-container>

      <app-container :key="name" v-for="(value, name) in tables">
        <app-section>
          <template #title
            ><i class="ti ti-file-spreadsheet mb-2"></i>{{ name }}</template
          >
          <PDataTable
            :value="value.changes"
            :paginator="value.changes.length > itemsPerPage"
            :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
            :rows="itemsPerPage"
            size="small"
            :scrollable="true"
            scroll-height="400px"
          >
            <template v-for="col in value.headers" :key="col.value">
              <!-- Show icon with insert / update / delete -->
              <PColumn
                v-if="col.value === 'operationTypeHeader'"
                :header="col.text"
                style="width: 50px"
                :pt="ptColumn"
              >
                <template #body="slotProps">
                  <app-circle
                    class="mr-1"
                    :severity="actions[slotProps.data[col.value]].severity"
                  >
                    <i
                      :class="[
                        'ti',
                        `${actions[slotProps.data[col.value]].icon}`
                      ]"
                    ></i>
                  </app-circle>
                </template>
              </PColumn>
              <!-- else show data -->
              <PColumn
                v-else
                :header="col.text"
                :style="{ minWidth: `${col.width}px` }"
                :pt="ptColumn"
              >
                <template #body="slotProps">{{
                  slotProps.data[col.value]
                }}</template>
              </PColumn>
            </template>
            <template #empty>
              <div class="flex flex-column align-items-center p-4 text-center">
                <p>No changeset for current layer</p>
              </div>
            </template>
          </PDataTable>
        </app-section>
      </app-container>
    </template>
    <app-container v-else-if="!loading">
      <app-section class="p-4">
        <div class="flex flex-column align-items-center text-center">
          <h3>Changes cannot be calculated</h3>
          <p>
            For details please check the
            <a
              class="font-semibold text-underline text-color-forest"
              :href="docsLinkManageSynchronisation"
              target="_blank"
              >documentation</a
            >.
          </p>
        </div>
      </app-section>
    </app-container>
  </div>
</template>

<script lang="ts">
import { AxiosResponse } from 'axios'
import groupBy from 'lodash/groupBy'
import isArray from 'lodash/isArray'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import AppCircle from '@/common/components/AppCircle.vue'
import AppContainer from '@/common/components/AppContainer.vue'
import AppSection from '@/common/components/AppSection.vue'
import { ProjectVersionFileChange, useNotificationStore } from '@/modules'
import { useInstanceStore } from '@/modules/instance/store'

interface ColumnItem {
  text: string
  value: string
  width: number
}

export default defineComponent({
  name: 'FileVersionDetailView',
  props: {
    namespace: String,
    projectName: String,
    version_id: String,
    path: String
  },
  data() {
    return {
      tables: null as Record<
        string,
        { headers?: ColumnItem[]; changes?: Record<string, string | number>[] }
      > | null,
      loading: false,
      actions: {
        insert: { icon: 'ti-plus', severity: 'success' },
        update: { icon: 'ti-pen', severity: 'warn' },
        delete: { icon: 'ti-trash', severity: 'danger' }
      },
      itemsPerPage: 10
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    docsLinkManageSynchronisation() {
      return `${this.configData?.docs_url ?? ''}/manage/synchronisation`
    },
    ptColumn() {
      return {
        headerCell: {
          style: {
            backgroundColor: '#F8F9FA'
          }
        },
        headerTitle: {
          class: 'paragraph-p6'
        }
      }
    }
  },
  created() {
    this.getChangeset()
  },
  methods: {
    ...mapActions(useNotificationStore, ['error']),
    // TODO: refactor to pinia action
    getChangeset() {
      this.loading = true
      this.$http
        .get(
          `/v1/resource/changesets/${this.namespace}/${this.projectName}/${this.version_id}?path=${this.path}`
        )
        .then((resp: AxiosResponse<ProjectVersionFileChange[]>) => {
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
              const arrayValue = value
              arrayValue.forEach((data) => {
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
                      row.new === undefined ? 'N/A' : row.new
                  } else if (data.type === 'update') {
                    if (typeof row.new === 'undefined') {
                      data.values[columnIdentifier] =
                        row.old === undefined ? 'N/A' : row.old
                    } else {
                      data.values[columnIdentifier] =
                        (row.old === undefined ? 'N/A' : row.old) +
                        ' ' +
                        String.fromCharCode(parseInt('2794', 16)) +
                        ' ' +
                        (row.new === undefined ? 'N/A' : row.new)
                    }
                  } else if (data.type === 'delete') {
                    data.values[columnIdentifier] =
                      row.old === undefined ? 'N/A' : row.old
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
        })
    }
  },
  components: { AppContainer, AppSection, AppCircle }
})
</script>
<style lang="scss" scoped></style>
