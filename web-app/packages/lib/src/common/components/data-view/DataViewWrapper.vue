<template>
  <div class="data-view-wrapper">
    <PDataView
      :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
      v-bind="$attrs"
      :value="value"
      :data-key="dataKey"
      @page="onPage"
    >
      <template #header>
        <div class="w-11 grid grid-nogutter">
          <!-- Visible on lg breakpoint > -->
          <div
            v-for="col in columns.filter((item) => !item.fixed)"
            :class="[
              'paragraph-p6 hidden lg:flex',
              `col-${col.cols ?? defaultCols}`
            ]"
            :key="col.text"
          >
            {{ col.text }}
          </div>
          <!-- else -->
          <div class="col-12 flex lg:hidden"><slot name="header-title" /></div>
        </div>
      </template>

      <template #list="slotProps">
        <!-- loading -->
        <div
          class="data-view-wrapper-loading bg-primary-reverse opacity-50"
          v-if="value.length && loading"
        >
          <PProgressSpinner style="width: 50px; height: 50px" />
        </div>

        <div
          v-for="item in slotProps.items"
          :key="item.id"
          :class="[
            'flex align-items-center hover:bg-gray-50 border-bottom-1 border-gray-200 paragraph-p6 px-4 py-2 mt-0',
            rowCursorPointer ? 'cursor-pointer' : ''
          ]"
          :style="[rowStyle?.(item)]"
          @click.prevent="!item.disabled && $emit('rowClick', item)"
        >
          <div class="flex-grow-1 grid grid-nogutter w-11">
            <!-- Columns, we are using data view instead table, it is better handling of respnsive state -->
            <div
              v-for="column in computedColumns.filter((item) => !item.fixed)"
              :key="column.value"
              :class="[
                'flex flex-column justify-content-center col-12 gap-1',
                `lg:col-${column.cols ?? defaultCols}`,
                'py-2 lg:py-0'
              ]"
            >
              <p class="paragraph-p6 opacity-80 font-semibold lg:hidden">
                {{ column.text }}
              </p>
              <slot :name="`col-${column.value}`" :column="column" :item="item">
                <span :class="[column.textClass || 'opacity-80']">{{
                  item[column.value]
                }}</span>
              </slot>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex w-1 flex-shrink-0 justify-content-end">
            <slot name="actions" :item="item"></slot>
          </div>
        </div>
      </template>

      <template #empty>
        <slot name="empty">
          <template v-if="loading !== undefined && loading">
            <div
              class="border-bottom-1 border-gray-200 px-4 py-2"
              v-for="i in loadingRows"
              :key="i"
            >
              <div class="flex-grow-1 grid grid-nogutter w-11">
                <div
                  v-for="col in columns.filter((item) => !item.fixed)"
                  :key="col.value"
                  :class="[
                    'flex flex-column justify-content-center col-12',
                    `lg:col-${col.cols ?? 2}`,
                    'py-2 pr-2'
                  ]"
                >
                  <PSkeleton />
                </div>
              </div>
            </div>
          </template>

          <div v-else class="w-full text-center p-4">
            <span>{{ emptyMessage }}</span>
          </div>
        </slot>
      </template>
    </PDataView>
  </div>
</template>

<script setup lang="ts">
import { DataViewPageEvent } from 'primevue/dataview'
import { computed, defineOptions, StyleValue } from 'vue'

import { DataViewWrapperColumnItem, DataViewWrapperOptions } from './types'

defineOptions({
  inheritAttrs: false
})

/**
 * Defines the props for the `DataViewWrapper` component.
 *
 * @interface Props
 * @property {string} dataKey - The key to use for identifying each item in the data.
 * @property {boolean} [loading] - Indicates whether the data is currently being loaded.
 * @property {number} [loadingRows] - The number of loading rows to display when the data is being loaded.
 * @property {string} [emptyMessage] - The message to display when there is no data available.
 * @property {DataViewWrapperColumnItem[]} columns - An array of column definitions for the data view.
 * @property {(item: any) => StyleValue} [rowStyle] - A function that returns the style for each row in the data view.
 * @property {boolean} [rowCursorPointer] - Indicates whether the cursor should be a pointer when hovering over a row.
 * @property {DataViewWrapperOptions} [options] - The options for the data view.
 * @property {object[]} [value] - The data to be displayed in the data view.
 */
/**
 * Defines the props for the `DataViewWrapper` component.
 *
 * @interface Props
 * @property {string} dataKey - The key to use for identifying each item in the data.
 * @property {boolean} [loading] - Indicates whether the data is currently being loaded.
 * @property {number} [loadingRows] - The number of loading rows to display when the data is being loaded.
 * @property {string} [emptyMessage] - The message to display when there is no data available.
 * @property {DataViewWrapperColumnItem[]} columns - An array of column definitions for the data view.
 * @property {(item: any) => StyleValue} [rowStyle] - A function that returns the style for each row in the data view.
 * @property {boolean} [rowCursorPointer] - Indicates whether the cursor should be a pointer when hovering over a row.
 * @property {DataViewWrapperOptions} [options] - The options for the data view.
 * @property {object[]} [value] - The data to be displayed in the data view.
 * @property {number} [defaultCols] - The default number of columns to display.
 */
interface Props {
  dataKey: string
  loading?: boolean
  loadingRows?: number
  emptyMessage?: string
  columns: DataViewWrapperColumnItem[]
  rowStyle?: (item) => StyleValue
  rowCursorPointer?: boolean
  options?: DataViewWrapperOptions
  value?: object[]
  defaultCols?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  loadingRows: 3,
  emptyMessage: 'No data available',
  rowCursorPointer: true,
  defaultCols: 2
})

type EmitItem = Record<string, unknown>

const emit = defineEmits<{
  (e: 'rowClick', item: EmitItem): void
  (e: 'update:options', options: DataViewWrapperOptions): void
}>()

const computedColumns = computed(() => {
  return props.columns.map((item) => {
    return {
      ...item,
      textClass: item.textClass || 'opacity-80'
    }
  })
})

const computedOptions = computed({
  get(): DataViewWrapperOptions {
    return props.options
  },
  set(value) {
    emit('update:options', value)
  }
})

function onPage(e: DataViewPageEvent) {
  computedOptions.value = {
    ...computedOptions.value,
    page: e.page + 1,
    itemsPerPage: e.rows
  }
}
</script>

<style scoped lang="scss">
.data-view-wrapper {
  position: relative;
}

.data-view-wrapper-loading {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  width: 100%;
  height: 100%;
}
</style>
