<template>
  <PAccordion
    multiple
    collapse-icon="ti ti-chevron-down"
    expand-icon="ti ti-chevron-right"
    :active-index="activeAccordionItems"
  >
    <PAccordionTab
      v-for="item in changeTabs"
      :key="item.key"
      :disabled="!changes[item.key].length"
    >
      <template #header>
        <app-circle :severity="item.severity" class="mr-2">
          <i :class="['ti', `${item.icon}`]"></i>
        </app-circle>
        <span class="paragraph-p5 opacity-80">{{ item.text }}</span>
        <app-circle class="ml-auto">
          {{ changes[item.key].length }}
        </app-circle></template
      >
      <div
        v-for="change in changes[item.key]"
        :key="change.path"
        class="paragraph-p6"
      >
        <div class="flex align-items-center justify-content-between mb-1">
          <span class="w-10 font-semibold">{{ change.path }}</span>
          <span class="flex-shrink-0">{{
            $filters.filesize(
              version.changesets?.[change.path]
                ? version.changesets?.[change.path]['size']
                : change.size
            )
          }}</span>
        </div>
        <template
          v-if="changesets?.[change.path] && !changesets?.[change.path].error"
          ><router-link
            class="text-color-forest text-underline font-semibold"
            :to="{
              name: 'file-version-detail',
              params: {
                namespace: version?.namespace,
                projectName: version?.project_name,
                version_id: version?.name,
                path: change?.path
              }
            }"
            >Show advanced</router-link
          >
          <file-changeset-summary-table
            :changesets="changesets?.[change.path]['summary']"
          />
        </template>
        <div
          v-else-if="
            changesets?.[change.path] && changesets?.[change.path].error
          "
          class="text-center"
        >
          Details not available:
          {{ changesets?.[change.path].error }}
        </div>
      </div>
    </PAccordionTab>
  </PAccordion>
</template>

<script lang="ts" setup>
import { ProjectVersion } from '@mergin/lib'
import { computed, ref, defineProps } from 'vue'

import AppCircle from '@/common/components/AppCircle.vue'
import FileChangesetSummaryTable from '@/modules/project/components/FileChangesetSummaryTable.vue'

const props = defineProps<{
  version: ProjectVersion
}>()

const changeTabs = ref<
  {
    key: 'added' | 'updated' | 'removed'
    severity: 'success' | 'warn' | 'danger'
    text: string
    icon: string
  }[]
>([
  {
    key: 'added',
    severity: 'success',
    text: 'Files added',
    icon: 'ti-plus'
  },
  {
    key: 'updated',
    severity: 'warn',
    text: 'Files edited',
    icon: 'ti-pencil'
  },
  {
    key: 'removed',
    severity: 'danger',
    text: 'Files removed',
    icon: 'ti-trash'
  }
])

const changes = computed(() => props.version?.changes)
const changesets = computed(() => props.version?.changesets)
const activeAccordionItems = computed<number[]>(() => {
  return changeTabs.value.reduce<number[]>((acc, tab, index) => {
    if (changes.value?.[tab.key].length > 0) {
      acc.push(index)
    }
    return acc
  }, [])
})
</script>
