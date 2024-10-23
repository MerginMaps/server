<template>
  <PDataView
    :value="items"
    :data-key="'path'"
    :paginator="items.length > itemPerPage"
    :sort-field="options.sortBy"
    :sort-order="options.sortDesc"
    :rows="itemPerPage"
    :paginator-template="'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink'"
    data-cy="file-browser-table"
  >
    <template #header>
      <div class="grid grid-nogutter">
        <div
          v-for="col in columns"
          :class="[`col-${col.cols ?? 3}`, 'paragraph-p6 hidden lg:flex']"
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
          :class="[`lg:col-${col.cols ?? 3}`, 'flex align-items-center col-12']"
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
            {{ $filters.timediff(item.mtime) }}
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
</template>

<script setup lang="ts">
import escapeRegExp from 'lodash/escapeRegExp'
import max from 'lodash/max'
import orderBy from 'lodash/orderBy'
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
  type?: string
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

const itemPerPage = 50

const columns: Column[] = [
  { text: 'Name', key: 'name', cols: 6 },
  { text: 'Modified', key: 'mtime' },
  { text: 'Size', key: 'size' }
]

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

const folders = computed(() => {
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
  if (props.search) {
    const regex = new RegExp(escapeRegExp(removeAccents(props.search)), 'i')
    // TODO: Replace with DataView sorting instead this order_by with lodash
    return orderBy(
      filterByLocation(projectFiles.value).filter(
        (f) => f.path.search(regex) !== -1
      ),
      props.options.sortBy,
      props.options.sortDesc < 0 ? 'desc' : 'asc'
    )
  }

  let result: FileItem[] = []
  if (props.location) {
    result.push({
      name: '..',
      type: 'folder',
      link: Path.normalize(Path.join(props.location, '..')),
      mtime: '',
      path: ''
    })
  }
  result = result.concat(folders.value, directoryFiles.value)
  return orderBy(
    result,
    props.options?.sortBy,
    props.options.sortDesc < 0 ? 'desc' : 'asc'
  )
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

function fileTreeView(file: FileItem) {
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
