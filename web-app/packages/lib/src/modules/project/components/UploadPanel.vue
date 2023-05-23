<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-card>
    <v-toolbar dense text theme="dark" color="primary">
      <v-toolbar-title>Data Sync</v-toolbar-title>
      <v-spacer />
      <v-btn icon @click="resetUpload">
        <v-icon>close</v-icon>
      </v-btn>
    </v-toolbar>

    <v-card-text v-if="upload.diff && upload.diff.changes">
      <v-layout class="stats-line">
        <label>Removed files:</label>
        <v-spacer />
        <span class="red--text">{{ upload.diff.removed.length }}</span>
        <v-icon small color="red">delete</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Added files:</label>
        <v-spacer />
        <span class="green--text">{{ upload.diff.added.length }}</span>
        <v-icon small color="green">add_circle</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Modified files:</label>
        <v-spacer />
        <span class="orange--text">{{ upload.diff.updated.length }}</span>
        <v-icon small color="orange">edit</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Upload data size:</label>
        <v-spacer />
        <span>{{ $filters.filesize(uploadSize) }}</span>
      </v-layout>
    </v-card-text>
    <v-card-text v-else-if="upload.diff">
      All files are up to date!
    </v-card-text>

    <v-card-text v-if="remainingAnalyzingFiles">
      <v-layout row>
        <v-progress-circular
          :size="30"
          :width="3"
          color="primary"
          indeterminate
        />
        <v-spacer />
        <span style="padding-right: 30px"
          >Remaining files: {{ remainingAnalyzingFiles }}</span
        >
      </v-layout>
    </v-card-text>

    <v-card-actions v-if="upload.diff && upload.diff.changes">
      <v-spacer />
      <action-button
        id="update-files-btn"
        @click="confirmUpload"
        :disabled="upload.running || remainingAnalyzingFiles > 0"
      >
        <template #icon>
          <cloud-upload-icon />
        </template>
        Update
      </action-button>
      <v-spacer />
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import axios from 'axios'
import pick from 'lodash/pick'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'
import { CloudUploadIcon } from 'vue-tabler-icons'

import ActionButton from '@/common/components/ActionButton.vue'
import { CHUNK_SIZE, isVersionedFile } from '@/common/mergin_utils'
import { useDialogStore, useNotificationStore } from '@/modules'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  data() {
    return {
      source: null
    }
  },
  props: {
    namespace: String
  },
  components: {
    ActionButton,
    CloudUploadIcon
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'uploads']),

    upload() {
      return this.uploads[this.project.path]
    },
    uploadSize() {
      if (this.upload) {
        const { added, updated } = this.upload.diff
        return added.concat(updated).reduce((sum, path) => {
          return sum + this.upload.files[path].size
        }, 0)
      }
      return 0
    },
    remainingAnalyzingFiles() {
      const list = (this.upload && this.upload.analysingFiles) || []
      return list.length
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['prompt']),
    ...mapActions(useNotificationStore, ['show']),
    ...mapActions(useProjectStore, [
      'setProject',
      'discardUpload',
      'startUpload',
      'pushProjectChanges',
      'pushProjectChunks',
      'pushFinishTransaction',
      'pushCancelTransaction'
    ]),

    resetUpload() {
      this.discardUpload({ projectPath: this.project.path })
      if (this.source) {
        this.source.cancel('Operation canceled by the user.')
        delete this.source
      }
    },
    async uploadChanges() {
      const { added, removed, updated } = this.upload.diff
      const fileInfoFields = ['path', 'checksum', 'size', 'mtime', 'chunks']
      const changes = {
        removed: removed.map((path) =>
          pick(this.project.files[path], fileInfoFields)
        ),
        added: added.map((path) =>
          pick(this.upload.files[path], fileInfoFields)
        ),
        updated: updated.map((path) =>
          pick(this.upload.files[path], fileInfoFields)
        )
      }

      const projectPath = this.project.path
      const version = this.project.version || 'v0'
      const resp = await this.pushProjectChanges({
        data: { version, changes },
        projectPath
      })
      const { transaction } = resp.data
      if (!transaction) {
        this.discardUpload({ projectPath })
        await this.show({
          text: 'Project updated'
        })
        this.setProject({ project: resp.data })
        return
      }

      this.source = axios.CancelToken.source()
      const promises = []
      added.concat(updated).forEach((path) => {
        this.upload.files[path].chunks.forEach((chunk, index) => {
          const file = this.upload.files[path].file
          const offset = index * CHUNK_SIZE
          const data = file.slice(offset, offset + CHUNK_SIZE)
          const p = new Promise((resolve) => {
            const pc = this.pushProjectChunks({
              chunk,
              data,
              projectPath,
              transaction,
              token: this.source.token
            })
            resolve(pc)
          })
          promises.push(p)
        })
      })

      // fire up chunks uploads
      this.startUpload()
      Promise.all(promises)
        .then(() => {
          // call server to finish upload transaction
          this.pushFinishTransaction({
            projectPath,
            token: this.source.token,
            transaction
          })
        })
        .catch((err) => {
          this.pushCancelTransaction({
            err,
            transaction
          })
        })
    },
    confirmUpload() {
      const props = {
        text: 'Changes from other users <strong> may get lost </strong> when uploading data from browser. It is highly recommended to use Mergin Maps QGIS plugin instead. <br> <br> Are you really sure you want to continue?',
        confirmText: 'Update'
      }
      const listeners = {
        confirm: () => this.uploadChanges()
      }

      if (this.upload.diff.updated.filter((i) => isVersionedFile(i)).length) {
        this.prompt({
          params: { props, listeners, dialog: { maxWidth: 500 } }
        })
      } else {
        this.uploadChanges()
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.v-card {
  min-width: 240px;
}

.stats-line {
  align-items: center;
  margin: 0.75em 0;

  label {
    font-weight: 500;
    color: #555;
  }

  .spacer {
    height: 1em;
    border-bottom: 1px dotted #ccc;
    margin: 0 0.5em;
  }

  .v-icon {
    margin: 0 0.25em;
  }
}
</style>
