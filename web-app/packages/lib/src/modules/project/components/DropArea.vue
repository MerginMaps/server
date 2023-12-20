<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div
    class="drop-area h-full"
    :class="{ active: dragOver }"
    @dragover.prevent="onDragOver"
    @dragleave.capture="setOver(false)"
    @drop.prevent="onDrop"
  >
    <div
      v-show="dragOver"
      class="drop-highlight lighten-3"
      :class="canDropFiles ? 'primary' : 'red'"
    />
    <div
      class="file-input"
      :class="canDropFiles ? '' : 'disabled'"
      @click="selectFiles()"
    >
      <input
        ref="selectFilesInput"
        @change="onFileSelected"
        type="file"
        name="files"
        multiple
      />
    </div>
    <slot>
      <div
        class="flex flex-column justify-content-center align-items-center text-center h-full p-4 pt-6"
      >
        <div
          class="text-2xl surface-section border-circle p-4 text-color-forest w-5rem h-5rem rotate-180"
        >
          <i class="ti ti-download" />
        </div>
        <h4 class="text-lg font-semibold text-color-forest">
          Drag and drop files
        </h4>
        <p class="text-sm opacity-80">
          You can drop files from your computer to start uploading
        </p>
      </div>
    </slot>
  </div>
</template>

<script lang="ts">
import debounce from 'lodash/debounce'
import keyBy from 'lodash/keyBy'
import pickBy from 'lodash/pickBy'
import Path from 'path'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { getFiles, checksum } from '@/common/mergin_utils'
import { useInstanceStore } from '@/modules/instance/store'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'

type ExtendedFile = File & { isFile: boolean }

export default defineComponent({
  props: ['location'],
  data() {
    return {
      dragOver: false
    }
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'uploads']),
    ...mapState(useInstanceStore, ['configData']),
    upload() {
      return this.project && this.uploads[this.project.name]
    },
    canDragOver() {
      return this.project && this.$route.name === 'project-tree'
    },
    canDropFiles() {
      const isUploadRunning = this.upload && this.upload.running
      return (
        this.canDragOver && !isUploadRunning && this.project.permissions.upload
      )
    }
  },
  methods: {
    ...mapActions(useNotificationStore, ['error']),
    ...mapActions(useProjectStore, [
      'initUpload',
      'uploadFiles',
      'finishFileAnalysis',
      'analysingFiles'
    ]),

    setOver: debounce(function (isOver) {
      this.dragOver = isOver
    }, 30),
    onDragOver() {
      if (!this.dragOver && this.canDragOver) {
        this.setOver(true)
      }
    },
    onDrop(evt) {
      this.setOver(false)
      if (!this.dragOver || !this.canDropFiles) {
        return
      }
      if (this.upload && this.upload.running) {
        return this.error({
          text: 'You cannot update files during upload'
        })
      }
      // prepare all entries because they will be not accessible after this callback ends (after 'await')
      const entries = Array.from(
        evt.dataTransfer.items as DataTransferItem[]
      ).map((i) => i.webkitGetAsEntry())
      if (entries.some((e) => e === null)) {
        return this.error({
          text: 'Drop only files or folders'
        })
      }
      this.createUpload(entries)
    },
    selectFiles() {
      if (this.canDropFiles) {
        this.$refs.selectFilesInput.click()
      }
    },
    onFileSelected(evt: Event) {
      // prepare all entries because they will be not accessible after this callback ends (after 'await')
      const entries = Array.from(
        (evt.target as HTMLInputElement).files as unknown as ExtendedFile[]
      ).map((i) => {
        i.isFile = true
        return i
      })
      this.partialDrop(this.location, entries)
      this.createUpload(entries)
    },

    async createUpload(entries) {
      let partial = true
      if (entries.length === 1) {
        const item = entries[0]
        if (item && item.isDirectory && item.name === this.project.name) {
          // whole project folder was dropped
          partial = false
        }
      }

      if (this.upload) {
        partial = true
      } else {
        // initialize new upload data
        this.initUpload({ files: partial ? this.project.files : null })
      }

      if (partial) {
        this.partialDrop(this.location, entries)
      } else {
        // TODO: check if upload already exists?
        const files = await getFiles(entries[0], this.configData)
        this.analysingFiles({ files: files.map((f) => f.path) })
        await this.analyzeFiles(files)
        this.uploadFiles({ files })
      }
    },

    async analyzeFiles(files) {
      // or compute checksums sequentially?
      // for (let file of files) {
      //   const hash = await checksum(file.file)
      //   file.checksum = hash
      //   this.finishFileAnalysis({ path: file.path })
      // }
      // return files

      return Promise.all(
        files.map(async (file) => {
          file.checksum = await checksum(file.file)
          this.finishFileAnalysis({ path: file.path })
        })
      )
    },
    async partialDrop(location, entries) {
      let uploadFiles
      if (this.upload) {
        uploadFiles = this.upload.files
      } else {
        uploadFiles = { ...this.project.files }
      }

      const items = []
      for (const entry of entries) {
        items.push({
          name: entry.name,
          isDirectory: entry.isDirectory,
          files: await getFiles(entry, this.configData)
        })
      }

      const allFiles = items.reduce((list, item) => list.concat(item.files), [])
      this.analysingFiles({ files: allFiles.map((f) => f.path) })
      await this.analyzeFiles(allFiles)

      items.forEach((entry) => {
        if (entry.isDirectory) {
          const directory = Path.join(location, entry.name)
          const pathPrefix = directory + '/'
          uploadFiles = {
            // filter all files in directory
            ...pickBy(uploadFiles, (file) => !file.path.startsWith(pathPrefix)),
            // new directory files
            ...keyBy(
              entry.files.map((f) => ({
                ...f,
                path: Path.join(directory, f.path)
              })),
              'path'
            )
          }
        } else {
          const file = entry.files[0]
          file.path = Path.join(location, file.path)
          uploadFiles = {
            ...uploadFiles,
            [file.path]: file
          }
        }
      })
      this.uploadFiles({ files: uploadFiles })
    }
  }
})
</script>

<style lang="scss" scoped>
.drop-area {
  position: relative;

  .drop-highlight {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 2px;
    z-index: 0;
    border: 2px solid currentColor;
  }

  .file-input {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    cursor: pointer;

    input[type='file'] {
      opacity: 0;
      max-width: 0;
      width: 0;
    }
  }

  .file-input.disabled {
    cursor: not-allowed;
  }
}
</style>
