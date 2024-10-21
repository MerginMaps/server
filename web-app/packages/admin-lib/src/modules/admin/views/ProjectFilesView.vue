<template>
  <div>
    <!-- Searching -->
    <app-container
      v-if="searchFilter !== '' || Object.keys(project?.files ?? {}).length > 0"
    >
      <app-section ground>
        <div class="flex align-items-center">
          <span class="p-input-icon-left flex-grow-1">
            <i class="ti ti-search paragraph-p3"></i>
            <PInputText
              placeholder="Search files"
              data-cy="search-files-field"
              v-model="searchFilter"
              class="w-full"
            />
          </span>
          <AppMenu :items="filterMenuItems" />
        </div>
      </app-section>
    </app-container>

    <app-container v-if="projectName">
      <app-section>
        <files-table
          :project-name="projectName"
          :namespace="namespace"
          :location="location"
          :options="options"
          :search="searchFilter"
          @row-click="rowClick"
        />
      </app-section>
    </app-container>
    <!-- Sidebars -->
    <file-detail-sidebar :namespace="namespace" :project-name="projectName" />
    <!-- notifications -->
    <upload-progress />
  </div>
</template>

<script setup lang="ts">
import {
  AppSection,
  AppContainer,
  AppMenu,
  useProjectStore,
  FilesTable,
  ProjectApi
} from '@mergin/lib'
import { storeToRefs } from 'pinia'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { ref, computed } from 'vue'

interface Props {
  namespace?: string
  projectName?: string
  location?: string
}

const props = withDefaults(defineProps<Props>(), {
  location: ''
})

const projectStore = useProjectStore()
const { project } = storeToRefs(projectStore)

const options = ref({
  sortBy: 'name',
  sortDesc: 1
})
const searchFilter = ref('')

const filterMenuItems = computed<MenuItem[]>(() => {
  const items = [
    { label: 'Sort by name A-Z', key: 'name', sortDesc: 1 },
    { label: 'Sort by name Z-A', key: 'name', sortDesc: -1 },
    { label: 'Sort by last modified', key: 'mtime', sortDesc: -1 },
    { label: 'Sort by file size', key: 'size', sortDesc: -1 }
  ]

  return items.map((item) => ({
    ...item,
    command: (e: MenuItemCommandEvent) => menuItemClick(e),
    class:
      options.value.sortBy === item.key &&
      options.value.sortDesc === item.sortDesc
        ? 'bg-primary-400'
        : ''
  }))
})

const rowClick = (file: { path: string }) => {
  // added random number to request avoid to browser caching files
  const url = ProjectApi.constructDownloadProjectFileUrl(
    props.namespace,
    props.projectName,
    encodeURIComponent(file?.path)
  )
  window.location.href = url
}

const menuItemClick = (e: MenuItemCommandEvent) => {
  options.value.sortBy = String(e.item.key)
  options.value.sortDesc = e.item.sortDesc
}
</script>

<style lang="scss" scoped></style>
