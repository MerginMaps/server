<template>
  <form @submit.prevent="download" class="flex flex-column pb-4 gap-2">
    <span class="p-input-filled">
      <label id="period-label">Period</label>
      <app-dropdown
        aria-labelledby="period-label"
        v-model="period"
        :options="periodOptions"
      />
    </span>

    <span class="p-input-filled w-full">
      <label for="range">Custom range</label>
      <PCalendar
        inputId="range"
        v-model="range"
        selectionMode="range"
        :disabled="Number(period) > -1"
        :max-date="maxDate"
        class="w-full"
        placeholder="Select date range"
      />
    </span>

    <!-- Footer -->
    <div
      class="w-full flex flex-column lg:flex-row justify-content-between align-items-center mt-4"
    >
      <PButton
        severity="secondary"
        @click="close"
        class="w-12 mb-2 lg:mb-0 lg:mr-2 lg:w-6"
        data-cy="clone-dialog-close-btn"
        label="Cancel"
      />
      <PButton
        type="submit"
        class="w-12 lg:w-6"
        label="Download"
        :disabled="range.filter(Boolean).length < 2"
      />
    </div>
  </form>
</template>

<script lang="ts" setup>
import { AppDropdown, DropdownOption, useDialogStore } from '@mergin/lib'
import subMonths from 'date-fns/subMonths'
import { ref, watchEffect } from 'vue'

import { useAdminStore } from '@/main'

const dialogStore = useDialogStore()
const adminStore = useAdminStore()

const maxDate = ref<Date>(new Date())
const period = ref<string>('3')
const periodOptions = ref<DropdownOption[]>([
  { label: 'Last 3 months', value: '3' },
  { label: 'Last 6 months', value: '6' },
  { label: 'Last 12 months', value: '12' },
  { label: 'Custom range', value: '-1' }
])
const range = ref<Array<Date>>([
  subMonths(new Date(), Number(period.value)),
  new Date()
])

watchEffect(() => {
  const periodValue = Number(period.value)
  if (periodValue < 0) {
    range.value = []
    return
  }
  range.value = [subMonths(new Date(), periodValue), new Date()]
})

function close() {
  dialogStore.closeDialog()
}

function download() {
  const [from, to] = range.value
  adminStore.downloadReport({ from, to })
}
</script>
