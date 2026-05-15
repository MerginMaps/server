// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import debounce from 'lodash/debounce'
import { DataTablePageEvent, DataTableSortEvent } from 'primevue/datatable'
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export interface DataTableSearchOptions {
  defaultSortBy?: string
  defaultSortDesc?: boolean
}

/**
 * Shared search/pagination/URL-sync logic for lazy-loaded admin data tables.
 *
 * Call setFetchFn() immediately after setup to register the table-specific
 * fetch action; all event handlers will invoke it automatically.
 */
export function useDataTableSearch(opts: DataTableSearchOptions = {}) {
  const { defaultSortBy = '', defaultSortDesc = false } = opts

  const route = useRoute()
  const router = useRouter()

  const search = ref('')
  const options = reactive({
    sortBy: [defaultSortBy] as string[],
    sortDesc: [defaultSortDesc] as boolean[],
    itemsPerPage: 20,
    page: 1,
    perPageOptions: [20, 50, 100]
  })
  const abortController = ref<AbortController | null>(null)
  const fetchFn = ref<((signal: AbortSignal) => void) | null>(null)

  function setFetchFn(fn: (signal: AbortSignal) => void) {
    fetchFn.value = fn
  }

  function initFromQuery() {
    const q = route.query
    if (q.q) search.value = String(q.q)
    if (q.page) options.page = Number(q.page)
    if (q.per_page) options.itemsPerPage = Number(q.per_page)
    if (q.order_by) options.sortBy[0] = String(q.order_by)
    if (q.desc) options.sortDesc[0] = q.desc === 'true'
  }

  function updateQuery() {
    const query: Record<string, string> = {}
    if (search.value) query.q = search.value
    if (options.page > 1) query.page = String(options.page)
    if (options.itemsPerPage !== 20)
      query.per_page = String(options.itemsPerPage)
    if (options.sortBy[0] && options.sortBy[0] !== defaultSortBy)
      query.order_by = options.sortBy[0]
    if (options.sortDesc[0] !== defaultSortDesc)
      query.desc = String(options.sortDesc[0])
    router.replace({ query })
  }

  function doFetch() {
    abortController.value?.abort()
    abortController.value = new AbortController()
    updateQuery()
    fetchFn.value?.(abortController.value.signal)
  }

  const onSearch = debounce(() => {
    options.page = 1
    doFetch()
  }, 500)

  function onPage(event: DataTablePageEvent) {
    options.page = event.page + 1
    options.itemsPerPage = event.rows
    doFetch()
  }

  function onSort(event: DataTableSortEvent) {
    options.sortBy[0] = event.sortField?.toString() ?? ''
    options.sortDesc[0] = event.sortOrder < 1
    doFetch()
  }

  function onRefresh() {
    doFetch()
  }

  return {
    search,
    options,
    abortController,
    setFetchFn,
    initFromQuery,
    doFetch,
    onSearch,
    onPage,
    onSort,
    onRefresh
  }
}
