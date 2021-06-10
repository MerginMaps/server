# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div
    class="drop-area"
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
      @click="selectFiles()">
      <input
        ref="selectFilesInput"
        @change="onFileSelected"
        type="file" name="files" multiple>
    </div>
    <slot/>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import debounce from 'lodash/debounce'
import pickBy from 'lodash/pickBy'
import keyBy from 'lodash/keyBy'
import Path from 'path'

import { getFiles, checksum } from '@/mergin'


export default {
  props: ['location'],
  data () {
    return {
      dragOver: false,
      pingData: null
    }
  },
  computed: {
    ...mapState(['project', 'uploads']),
    upload () {
      return this.project && this.uploads[this.project.name]
    },
    canDragOver () {
      return this.project && this.$route.name === 'project-tree'
    },
    canDropFiles () {
      const isUploadRunning = this.upload && this.upload.running
      return this.canDragOver && !isUploadRunning && this.project.permissions.upload
    }
  },
  created () {
    this.getPingData()
  },
  methods: {
    getPingData () {
      this.$http.get('/ping')
        .then(resp => {
          this.pingData = resp.data
        })
        .catch(() => {
          this.$notification.error('Failed to ping server')
        })
    },
    setOver: debounce(function (isOver) {
      this.dragOver = isOver
    }, 30),
    onDragOver () {
      if (!this.dragOver && this.canDragOver) {
        this.setOver(true)
      }
    },
    onDrop (evt) {
      this.setOver(false)
      if (!this.dragOver || !this.canDropFiles) {
        return
      }
      if (this.upload && this.upload.running) {
        return this.$notification.error('You cannot update files during upload')
      }
      // prepare all entries cause they will be not accessible after this callback ends (after 'await')
      const entries = Array.from(evt.dataTransfer.items).map(i => i.webkitGetAsEntry())
      if (entries.some(e => e === null)) {
        return this.$notification.error('Drop only files or folders')
      }
      this.createUpload(entries)
    },
    selectFiles () {
      if (this.canDropFiles) {
        this.$refs.selectFilesInput.click()
      }
    },
    onFileSelected (evt) {
      // prepare all entries cause they will be not accessible after this callback ends (after 'await')
      const entries = Array.from(evt.target.files).map(i => {
        i.isFile = true
        return i
      })
      this.partialDrop(this.location, entries)
      this.createUpload(entries)
    },

    async createUpload (entries) {
      let partial = true
      if (entries.length === 1) {
        const item = entries[0]
        if (item && item.isDirectory && item.name === this.project.name) {
          // whole project folder was dropped
          partial = false
        }
      }

      if (!this.upload) {
        // initialize new upload data
        this.$store.commit('upload', partial ? this.project.files : {})
      } else {
        partial = true
      }

      if (partial) {
        this.partialDrop(this.location, entries)
      } else {
        // TODO: check if upload already exists?
        const files = await getFiles(entries[0], this.pingData)
        this.$store.commit('analysingFiles', files.map(f => f.path))
        await this.analyzeFiles(files)
        this.$store.commit('uploadFiles', files)
      }
    },

    async analyzeFiles (files) {
      // or compute checksums sequentially?
      // for (let file of files) {
      //   const hash = await checksum(file.file)
      //   file.checksum = hash
      //   this.$store.commit('finishFileAnalysis', file.path)
      // }
      // return files

      return Promise.all(files.map(async (file) => {
        const hash = await checksum(file.file)
        file.checksum = hash
        this.$store.commit('finishFileAnalysis', file.path)
      }))
    },
    async partialDrop (location, entries) {
      let uploadFiles
      if (!this.upload) {
        // this.$store.commit('upload')
        uploadFiles = { ...this.project.files }
      } else {
        uploadFiles = this.upload.files
      }

      const items = []
      for (const entry of entries) {
        items.push({
          name: entry.name,
          isDirectory: entry.isDirectory,
          files: await getFiles(entry, this.pingData)
        })
      }

      const allFiles = items.reduce((list, item) => list.concat(item.files), [])
      this.$store.commit('analysingFiles', allFiles.map(f => f.path))
      await this.analyzeFiles(allFiles)

      items.forEach(entry => {
        if (entry.isDirectory) {
          const directory = Path.join(location, entry.name)
          const pathPrefix = directory + '/'
          uploadFiles = {
            // filter all files in directory
            ...pickBy(uploadFiles, file => !file.path.startsWith(pathPrefix)),
            // new directory files
            ...keyBy(entry.files.map(f => ({ ...f, path: Path.join(directory, f.path) })), 'path')
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
      this.$store.commit('uploadFiles', uploadFiles)
    }
  }
}
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

    input[type=file] {
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
