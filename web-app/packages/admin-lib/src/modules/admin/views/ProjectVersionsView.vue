<template>
  <app-container>
    <app-section ground class="flex justify-content-end">
      <AppMenu :items="filterMenuItems" />
    </app-section>
    <app-section>
      <project-versions-table
        :project-name="projectName"
        :namespace="namespace"
        v-model:options="options"
        @row-click="rowClick"
      >
        <template #col-name="{ item }">
          <router-link
            :to="{
              name: 'project-version',
              params: {
                namespace: item.namespace,
                projectName: item.project_name,
                version_id: item.name
              }
            }"
            >{{ item.name }}</router-link
          >
        </template>
      </project-versions-table>
    </app-section>
  </app-container>
</template>

<script setup lang="ts">
import {
  AppSection,
  AppContainer,
  AppMenu,
  ProjectVersionsTable,
  DataViewWrapperOptions,
  ProjectVersionsTableItem
} from '@mergin/lib'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  projectName?: string
  namespace?: string
}

defineProps<Props>()

const router = useRouter()

const options = ref<DataViewWrapperOptions>({
  sortDesc: true,
  itemsPerPage: 50,
  page: 1
})

const filterMenuItems = computed<MenuItem[]>(() => {
  return [
    {
      label: 'Newest versions',
      key: 'newest',
      sortDesc: true
    },
    {
      label: 'Oldest versions',
      key: 'oldest',
      sortDesc: false
    }
  ].map((item) => ({
    ...item,
    command: (e: MenuItemCommandEvent) => menuItemClick(e),
    class: options.value.sortDesc === item.sortDesc ? 'bg-primary-400' : ''
  }))
})

const rowClick = (item: ProjectVersionsTableItem) => {
  router.push({
    path: `history/${item.name}`
  })
}

const menuItemClick = (e: MenuItemCommandEvent) => {
  options.value.sortDesc = e.item.sortDesc
}
</script>

<style lang="scss" scoped></style>
