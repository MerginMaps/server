<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PDialog
    v-model:visible="visible"
    :position="isUnderOverlayBreakpoint ? 'topleft' : 'bottomright'"
    class="upload-panel w-8 lg:w-3"
    :draggable="false"
  >
    <template #header>
      <p class="font-semibold">
        Data Sync
        <span v-if="upload.diff" class="text-color-secondary"
          >({{ $filters.filesize(uploadSize) }})</span
        >
      </p>
    </template>
    <div v-if="upload.diff && upload.diff.changes">
      <div
        class="flex py-1 align-items-center"
        v-for="key in ['added', 'updated', 'removed']"
        :key="key"
      >
        <app-circle :severity="circleSeverity[key]" class="mr-2"
          ><i :class="['ti', `${diffIcon[key]}`]"></i
        ></app-circle>
        <span class="paragraph-p5 opacity-80 capitalize">{{ key }}</span>
        <app-circle class="ml-auto">{{ upload.diff[key].length }}</app-circle>
      </div>
      <PButton
        id="update-files-btn"
        @click="confirmUpload"
        :disabled="upload.running || remainingAnalyzingFiles > 0"
        class="mt-2 w-full my-4"
        label="Update Changes"
      />
    </div>
  </PDialog>
</template>

<script lang="ts">
import axios from 'axios'
import pick from 'lodash/pick'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import AppCircle from '@/common/components/AppCircle.vue'
import { CHUNK_SIZE, isVersionedFile } from '@/common/mergin_utils'
import {
  ConfirmDialog,
  ConfirmDialogProps,
  useDialogStore,
  useLayoutStore,
  useNotificationStore
} from '@/modules'
import { useProjectStore } from '@/modules/project/store'

type DiffKeys = 'removed' | 'added' | 'updated'

export default defineComponent({
  data() {
    return {
      source: null
    }
  },
  props: {
    namespace: String
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'uploads']),
    ...mapState(useLayoutStore, ['isUnderOverlayBreakpoint']),
    visible: {
      get() {
        return !!this.upload
      },
      set(visible) {
        if (visible) return visible
        this.resetUpload()
      }
    },
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
    },
    diffIcon() {
      const icons: Record<DiffKeys, string> = {
        removed: 'ti-trash',
        added: 'ti-plus',
        updated: 'ti-pencil'
      }
      return icons
    },
    circleSeverity() {
      const severities: Record<DiffKeys, 'success' | 'warn' | 'danger'> = {
        removed: 'danger',
        added: 'success',
        updated: 'warn'
      }
      return severities
    }
  },
  methods: {
    ...mapActions(useDialogStore, { showDialog: 'show' }),
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
      const props: ConfirmDialogProps = {
        text: `Are you really sure you want to continue?`,
        description:
          'Changes from other users may get lost when uploading data from browser. It is highly recommended to use Mergin Maps QGIS plugin instead.',
        confirmText: 'Update',
        cancelText: 'Cancel'
      }
      const listeners = {
        confirm: () => this.uploadChanges()
      }
      if (this.upload.diff.updated.filter((i) => isVersionedFile(i)).length) {
        this.showDialog({
          component: ConfirmDialog,
          params: {
            props,
            listeners,
            dialog: { maxWidth: 500, header: 'Confirm continue upload' }
          }
        })
      } else {
        this.uploadChanges()
      }
    }
  },
  components: { AppCircle }
})
</script>

<style lang="scss" scoped></style>
