<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div class="mt-2">
    <PDataView
      :value="displayedChangeset"
      :data-key="'table'"
      :paginator="displayedChangeset.length > itemsPerPage"
      :rows="itemsPerPage"
      :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
      :pt="{
        root: {
          class: 'border-round-xl'
        },
        header: {
          class: 'px-4 py-2'
        }
      }"
    >
      <template #header>
        <div class="grid grid-nogutter">
          <div v-for="col in columns" class="col-3 text-xs" :key="col.text">
            <i
              v-if="col.icon"
              :class="['ti', `ti-${col.icon}`]"
              v-tooltip.top="col.text"
            ></i>
            <span v-else>{{ col.text }}</span>
          </div>
        </div>
      </template>
      <template #list="slotProps">
        <div
          v-for="item in slotProps.items"
          :key="item.id"
          class="grid grid-nogutter px-4 py-2 mt-0 border-bottom-1 border-gray-200 text-sm hover:bg-gray-200 cursor-pointer"
        >
          <div
            v-for="col in columns"
            class="flex align-items-center col-3"
            :key="col.value"
          >
            {{ item[col.value] }}
          </div>
        </div>
      </template>
    </PDataView>
  </div>
</template>

<script lang="ts">
import { PropType, defineComponent } from 'vue'

import { ChangesetSuccessSummaryItem } from '../types'

export default defineComponent({
  name: 'file-changeset-summary-table',
  props: {
    changesets: Array as PropType<ChangesetSuccessSummaryItem[]>
  },
  data() {
    return {
      columns: [
        { text: 'Layer', value: 'table' },
        {
          text: 'Inserts',
          icon: 'plus',
          value: 'insert'
        },
        { text: 'Updates', icon: 'pencil', value: 'update' },
        { text: 'Deletes', icon: 'trash', value: 'delete' }
      ],
      itemsPerPage: 10
    }
  },
  computed: {
    displayedChangeset() {
      // Displayed changesets data into table data
      return this.changesets.filter((p) => p.table !== 'gpkg_contents')
    }
  }
})
</script>

<style lang="scss" scoped></style>
