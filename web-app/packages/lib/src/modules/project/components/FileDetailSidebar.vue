<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <AppSidebarRight v-model="sidebarVisible">
      <template #title>{{ fileName }}</template>
      <template #headerButtons
        ><PButton
          type="button"
          @click="downloadFile"
          icon="ti ti-download"
          text
          rounded
          plain
          class="p-1 text-2xl"
          data-cy="file-detail-download-btn"
        ></PButton
      ></template>

      <div class="overflow-y-auto">
        <PInlineMessage v-if="state" :severity="stateSeverity" class="w-full">
          {{ stateText }}
        </PInlineMessage>

        <dl class="grid grid-nogutter row-gap-4">
          <div class="col-12">
            <dt class="text-xs opacity-80 mb-2">File</dt>
            <dl class="font-semibold">
              <h3 class="text-2xl mt-0">
                <FileIcon :file="{ ...file, name: fileName }" />{{ fileName }}
              </h3>
            </dl>
          </div>
          <PDivider class="m-0" />
          <div class="col-6">
            <dt class="text-xs opacity-80 mb-2">Modified</dt>
            <dl class="font-semibold text-sm">
              <span v-tooltip="$filters.datetime(file.mtime)">{{
                $filters.timediff(file.mtime)
              }}</span>
            </dl>
          </div>
          <div class="col-6 flex flex-column align-items-end">
            <dt class="text-xs opacity-80 mb-2">Size</dt>
            <dl class="font-semibold text-sm">
              {{ $filters.filesize(file.size) }}
              <span v-if="state === 'updated'"
                >(new:
                {{ $filters.filesize(upload.files[file.path].size) }})</span
              >
            </dl>
          </div>
        </dl>

        <!--     render only if file is smaller than 100MB-->
        <output
          v-if="mimetype && file.size < 104857600"
          class="flex flex-column align-items-center w-full py-4"
        >
          <PImage
            :src="downloadUrl"
            v-if="mimetype.match('image')"
            preview
            imageClass="w-full"
          />
          <div
            class="file-detail-code border-round-xl p-4 line-height-3 w-full"
            v-else-if="mimetype.match('text')"
          >
            <span class="opacity-80 text-sm">{{ content }}</span>
          </div>
        </output>
      </div>

      <!-- foooter -->
      <template #footer>
        <PButton
          v-if="project && project.permissions.upload && state !== 'removed'"
          severity="danger"
          @click="removeSelected"
          class="flex justify-content-center w-full text-center"
          data-cy="file-detail-remove-btn"
        >
          Delete file
        </PButton>
      </template>
    </AppSidebarRight>
  </div>
</template>

<script lang="ts">
import Path from 'path'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import FileIcon from './FileIcon.vue'

import AppSidebarRight from '@/common/components/AppSidebarRight.vue'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'

enum State {
  ADDED = 'added',
  REMOVED = 'removed',
  UPDATED = 'updated'
}

export default defineComponent({
  name: 'FileDetailSidebar',
  props: {
    namespace: String,
    projectName: String
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'uploads']),
    upload() {
      return this.uploads[this.project.path]
    },
    file() {
      return (
        this.project?.files[this.filePath] || this.upload?.files[this.filePath]
      )
    },
    fileName() {
      return Path.basename(this.file?.path)
    },
    downloadUrl() {
      // added random number to request avoid to browser caching files
      return ProjectApi.constructDownloadProjectFileUrl(
        this.namespace,
        this.projectName,
        encodeURIComponent(this.file?.path)
      )
    },
    state(): State {
      const diff = this.upload && this.upload.diff
      if (diff) {
        const path = this.file?.path
        if (diff.added.includes(path)) {
          return State.ADDED
        } else if (diff.removed.includes(path)) {
          return State.REMOVED
        } else if (diff.updated.includes(path)) {
          return State.UPDATED
        }
      }
      return null
    },
    stateSeverity() {
      const stateSeverity: Record<State, string> = {
        added: 'success',
        removed: 'error',
        updated: 'info'
      }
      return this.state && stateSeverity[this.state]
    },
    stateText() {
      const stateText: Record<State, string> = {
        added: 'New file',
        removed: 'Deleted file',
        updated: 'Modified file'
      }
      return this.state && stateText[this.state]
    },
    filePath(): string {
      return this.$route.query.file_path as string
    },
    sidebarVisible: {
      get() {
        return !!this.filePath
      },
      set(visible: boolean) {
        if (visible) {
          this.sidebarVisible = visible
        } else {
          this.$router.replace({ query: undefined })
        }
      }
    }
  },
  data() {
    return {
      previewUrl: '',
      pageCount: 0,
      currentPage: 0,
      content: null,
      mimetype: null as string
    }
  },
  watch: {
    file: {
      immediate: true,
      handler() {
        if (this.file) {
          this.txtPreview()
          return
        }
        this.sidebarVisible = false
      }
    }
  },
  methods: {
    ...mapActions(useProjectStore, ['deleteFiles']),
    txtPreview() {
      ProjectApi.getProjectFileByUrl(this.downloadUrl).then((resp) => {
        this.mimetype = resp.headers['content-type']
        if (resp.headers['content-type'].match('text')) {
          if (resp.data.constructor === Object) {
            resp.data = JSON.stringify(resp.data)
          }
          this.content = resp.data.match(/^.*([^\n]*\n){0,50}/gi)[0]
          if (!this.content) {
            this.content = ''
            return
          }
          if (this.content.length > 10000) {
            this.content = this.content.substring(0, 10000)
          }
        } else {
          this.content = null
        }
      })
    },
    removeSelected() {
      this.deleteFiles({ files: [this.file.path] })
    },
    downloadFile() {
      window.location.href = this.downloadUrl
    }
  },
  components: { AppSidebarRight, FileIcon }
})
</script>

<style lang="scss" scoped>
.file-detail {
  &-code {
    background-color: var(--light-green-color);
    word-wrap: break-word;
  }
}
</style>
