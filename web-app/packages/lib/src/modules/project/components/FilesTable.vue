<template>
  <div>
    <PBreadcrumb
      :model="breadcrumps"
      :pt="{
        root: {
          style: {
            backgroundColor: 'transparent'
          },
          class: 'border-none p-4 w-full overflow-x-auto'
        }
      }"
    >
      <template #separator>
        <i class="ti ti-slash" />
      </template>
      <template #item="{ item, props }">
        <router-link
          v-if="item.path"
          v-slot="{ href, navigate }"
          :to="{
            path: item.path
          }"
          custom
        >
          <a :href="href" v-bind="props.action" @click="navigate">
            <span :class="[item.icon, 'paragraph-p6']" />
            {{ '&nbsp;' }}
            <span
              :class="[
                'opacity-80 paragraph-p6',
                item.active ? 'text-color-forest font-semibold' : 'text-color'
              ]"
              >{{ item.label }}</span
            >
          </a>
        </router-link>
      </template>
    </PBreadcrumb>
    <PDataView
      :value="items"
      :data-key="'path'"
      :paginator="items.length > ITEMS_PER_PAGE"
      :sort-field="options.sortBy"
      :sort-order="options.sortDesc"
      :rows="ITEMS_PER_PAGE"
      :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
      data-cy="file-browser-table"
    >
      <template #header>
        <div class="grid grid-nogutter">
          <div
            v-for="col in columns"
            :class="[`col-${col.cols ?? 2}`, 'paragraph-p6 hidden lg:flex']"
            :key="col.text"
          >
            {{ col.text }}
          </div>
          <div class="col-12 flex lg:hidden">Files</div>
        </div>
      </template>
      <template #list="slotProps">
        <div
          v-for="item in slotProps.items"
          :key="item.id"
          class="grid grid-nogutter px-4 py-3 mt-0 border-bottom-1 border-gray-200 paragraph-p6 hover:bg-gray-50 cursor-pointer row-gap-2"
          @click.prevent="rowClick(item)"
        >
          <div
            v-for="col in columns"
            :class="[
              `lg:col-${col.cols ?? 2}`,
              'flex align-items-center col-12'
            ]"
            :key="col.key"
          >
            <span
              v-if="col.key === 'name'"
              class="font-semibold mb-2 lg:mb-0 m-0"
            >
              <file-icon :file="item" />{{ item.name }}
            </span>
            <span
              v-else-if="col.key === 'mtime'"
              v-tooltip.bottom="{ value: $filters.datetime(item.mtime) }"
              class="opacity-80"
            >
              {{ item.mtime ? $filters.timediff(item.mtime) : '' }}
            </span>
            <span v-else class="opacity-80">{{
              item.size !== undefined ? $filters.filesize(item.size) : ''
            }}</span>
          </div>
        </div>
      </template>
      <template #empty>
        <div class="w-full text-center p-4">
          <span>No files found.</span>
        </div>
      </template>
    </PDataView>
  </div>
</template>

<script setup lang="ts">
import escapeRegExp from 'lodash/escapeRegExp'
import max from 'lodash/max'
import Path from 'path'
import { computed } from 'vue'

import { dirname } from '@/common/path_utils'
import { removeAccents } from '@/common/text_utils'
import FileIcon from '@/modules/project/components/FileIcon.vue'
import { useProjectStore } from '@/modules/project/store'

interface Column {
  text: string
  key: string
  cols?: number
}

interface FileItem {
  name?: string
  path: string
  type?: 'folder' | 'file'
  link?: string
  size?: number
  mtime?: string
  flags?: {
    added?: boolean
    updated?: boolean
    removed?: boolean
  }
}

const props = defineProps<{
  namespace: string
  projectName: string
  location: string
  search: string
  options: {
    sortBy: string
    sortDesc: number
  }
}>()
const emit = defineEmits<{
  (e: 'rowClick', item: FileItem): void
}>()

const projectStore = useProjectStore()

const ITEMS_PER_PAGE = 100

const columns: Column[] = [
  { text: 'Name', key: 'name', cols: 8 },
  { text: 'Modified', key: 'mtime' },
  { text: 'Size', key: 'size' }
]

const breadcrumps = computed(() => {
  const location = props.location
  const parts = location.split('/').filter(Boolean)
  let path = ''
  const result = parts.map((part, index) => {
    path = Path.join(path, part)
    return {
      label: part,
      path: folderLink(path),
      active: index === parts.length - 1
    }
  })
  return [
    {
      icon: 'ti ti-folder',
      label: 'Project home',
      path: folderLink(''),
      active: parts.length === 0
    },
    ...result
  ]
})

const projectFiles = computed(() => {
  let files = projectStore.project.files
  if (projectStore.uploads[projectStore.project.path] && diff.value) {
    files = {
      ...files,
      ...projectStore.uploads[projectStore.project.path].files
    }
  }
  return Object.values<FileItem>(files).map(fileTreeView)
})

const directoryFiles = computed(() => {
  return projectFiles.value.filter(
    (file) => dirname(file.path) === props.location
  )
})

const folders = computed<FileItem[]>(() => {
  const folders: { [key: string]: FileItem[] } = {}
  const prefix = props.location ? escapeRegExp(props.location + '/') : ''
  const regex = new RegExp(`^${prefix}([^/]+)/`)
  projectFiles.value.forEach((f) => {
    const m = f.path.match(regex)
    if (m) {
      const name = m[1]
      if (folders[name]) {
        folders[name].push(f)
      } else {
        folders[name] = [f]
      }
    }
  })
  return Object.keys(folders)
    .sort()
    .map((name) => {
      const path = Path.join(props.location, name)
      const files = folders[name]
      return {
        name,
        path,
        files,
        type: 'folder',
        link: folderLink(path),
        size: files.reduce((sum, f) => sum + (f.size || 0), 0),
        mtime: max(files, (f) => f.mtime)?.mtime || '',
        flags: folderFlags(files),
        diffStats: diff.value ? folderDiffStats(files) : null
      }
    })
})

const diff = computed(() => {
  const upload = projectStore.uploads[projectStore.project.path]
  const diff = upload && upload.diff
  if (diff && diff.changes) {
    return {
      ...diff
    }
  }
  return null
})

function filterByLocation(files) {
  let dirPrefix = ''
  if (props.location) {
    dirPrefix = props.location.replace(/\/$/, '') + '/'
    files = files.filter((file) =>
      (dirname(file.path) + '/').startsWith(dirPrefix)
    )
  }
  return files.map((f) => ({ ...f, name: f.path.slice(dirPrefix.length) }))
}

const items = computed(() => {
  const result: FileItem[] = [...folders.value, ...directoryFiles.value]
  if (props.search) {
    const regex = new RegExp(escapeRegExp(removeAccents(props.search)), 'i')
    return filterByLocation(result).filter((f) => f.path.search(regex) !== -1)
  }

  return result
})

function fileFlags(file: FileItem) {
  return (
    diff.value && {
      added: diff.value.added.includes(file.path),
      updated: diff.value.updated.includes(file.path),
      removed: diff.value.removed.includes(file.path)
    }
  )
}

function folderFlags(files: FileItem[]) {
  return (
    diff.value && {
      added: files.every((f) => diff.value?.added.includes(f.path)),
      removed: files.every((f) => diff.value?.removed.includes(f.path))
    }
  )
}

function folderDiffStats(files: FileItem[]) {
  if (!diff.value) return null
  const { added, removed, updated } = diff.value
  return {
    added: files.filter((f) => added.includes(f.path)).length,
    removed: files.filter((f) => removed.includes(f.path)).length,
    updated: files.filter((f) => updated.includes(f.path)).length,
    count: files.length
  }
}

function fileTreeView(file): FileItem {
  const filename = Path.basename(file.path)
  return {
    ...file,
    type: 'file',
    name: filename,
    link: fileLink(file),
    flags: fileFlags(file)
  }
}

function fileLink(file: FileItem) {
  return `/projects/${props.namespace}/${
    props.projectName
  }/blob/${encodeURIComponent(file.path)}`
}

function folderLink(path: string) {
  return `/projects/${props.namespace}/${props.projectName}/tree/${path}`
}

function rowClick(item: FileItem) {
  emit('rowClick', item)
}
</script>
