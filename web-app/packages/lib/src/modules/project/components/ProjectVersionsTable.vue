<template>
  <DataViewWrapper
    lazy
    :rows="options.itemsPerPage"
    :totalRecords="versionsCount"
    :columns="columns"
    :value="items"
    :data-key="'name'"
    :options="options"
    :loading="versionsLoading"
    :row-style="rowStyle"
    @update:options="updateOptions"
    @row-click="(item) => rowClick(item as unknown as ProjectVersionsTableItem)"
    :paginator="
      showPagination && options && versionsCount > options.itemsPerPage
    "
    data-cy="project-version-table"
    :empty-message="t('NoVersionsFound')"
  >
    <template #header-title>{{ t('Versions') }}</template>

    <template #actions="{ item }">
      <PButton
        icon="ti ti-download"
        rounded
        plain
        text
        :disabled="item.disabled"
        :style="rowStyle(item)"
        class="paragraph-p3"
        data-cy="project-versions-download-btn"
        @click.stop="downloadClick(item)"
      />
    </template>

    <template #col-name="{ item, column }">
      <p :class="['title-t4', column.textClass]">
        <slot name="col-name" :item="item" :column="column">
          <router-link :to="{ query: { version_id: item.name } }">{{
            item.name
          }}</router-link>
        </slot>
      </p>
    </template>
    <template #col-created="{ column, item }">
      <span
        v-tooltip.left="{
          value: $filters.datetime(item.created)
        }"
        :class="column.textClass"
      >
        {{ $filters.timediff(item.created) }}
      </span>
    </template>
    <template #col-project_size="{ item, column }">
      <span :class="column.textClass">{{
        $filters.filesize(item.project_size)
      }}</span>
    </template>
    <template #col-changes.added="{ item, column }">
      <span :class="column.textClass">{{ item.changes.added }}</span>
    </template>
    <template #col-changes.updated="{ item, column }">
      <span :class="column.textClass">{{
        item.changes.updated + item.changes.updated_diff
      }}</span>
    </template>
    <template #col-changes.removed="{ item, column }">
      <span :class="column.textClass">{{ item.changes.removed }}</span>
    </template>
  </DataViewWrapper>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { ref, computed, StyleValue, watch } from 'vue'

import returnTranslation from '@/../../lang/translate'
import DataViewWrapper from '@/common/components/data-view/DataViewWrapper.vue'
import {
  DataViewWrapperColumnItem,
  DataViewWrapperOptions
} from '@/common/components/data-view/types'
import {
  FetchProjectVersionsParams,
  ProjectApi,
  ProjectVersionsTableItem
} from '@/modules'
import { useProjectStore } from '@/modules/project/store'

const props = withDefaults(
  defineProps<{
    projectName: string
    namespace: string
    disabledKeys?: string[]
    showPagination?: boolean
    options: DataViewWrapperOptions
  }>(),
  { disabledKeys: () => [], showPagination: true, onRowClick: null }
)

const emit = defineEmits<{
  (e: 'update:options', options: DataViewWrapperOptions): void
  (e: 'rowClick', item: ProjectVersionsTableItem): void
}>()

const projectStore = useProjectStore()
const { versions, versionsLoading, versionsCount, project } =
  storeToRefs(projectStore)
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const columns = ref<DataViewWrapperColumnItem[]>([
  {
    text: t('Version'),
    value: 'name',
    textClass: 'white-space-normal',
    cols: 1
  },
  { text: t('Created'), value: 'created' },
  { text: t('Author'), value: 'author' },
  { text: t('FilesAdded'), value: 'changes.added' },
  { text: t('FilesEdited'), value: 'changes.updated' },
  { text: t('FilesRemoved'), value: 'changes.removed' },
  { text: t('Size'), value: 'project_size', cols: 1 },
  { text: '', value: 'archived', fixed: true }
])

const items = computed<ProjectVersionsTableItem[]>(() =>
  versions.value?.map<ProjectVersionsTableItem>((v) => ({
    ...v,
    disabled: props.disabledKeys.some((d) => d === v.name)
  }))
)

const rowStyle = (item: ProjectVersionsTableItem): StyleValue =>
  item.disabled ? ({ opacity: 0.5, cursor: 'not-allowed' } as StyleValue) : {}

const fetchVersions = async () => {
  const params: FetchProjectVersionsParams = {
    page: props.options.page,
    per_page: props.options.itemsPerPage,
    descending: props.options.sortDesc
  }
  await projectStore.getProjectVersions({
    params,
    projectName: props.projectName,
    workspace: props.namespace
  })
}

const rowClick = (item: ProjectVersionsTableItem) => {
  emit('rowClick', item)
}

const updateOptions = (newOptions: DataViewWrapperOptions) => {
  emit('update:options', newOptions)
}

const downloadClick = (item: ProjectVersionsTableItem) => {
  projectStore.downloadArchive({
    url: ProjectApi.constructDownloadProjectVersionUrl(
      project.value.id,
      item.name
    ),
    versionId: item.name
  })
}

watch(() => props.options, fetchVersions, { deep: true })

fetchVersions()
</script>
