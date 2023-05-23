<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <div v-if="state" v-text="stateText" :class="['status', colors[state]]" />
    <action-button
      v-if="project && project.permissions.upload && this.state !== 'removed'"
      @click="removeSelected"
      data-cy="file-detail-remove-btn"
      style="float: right"
      colorClass="red"
    >
      <template #icon>
        <trash-icon />
      </template>
      Remove file
    </action-button>
    <action-button
      :disabled="state === 'added'"
      :href="downloadLink"
      data-cy="file-detail-download-btn"
      style="float: right"
    >
      <template #icon>
        <download-icon />
      </template>
      Download File
    </action-button>

    <v-list two-line subheader>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Name</v-list-item-title>
          <v-list-item-subtitle>{{ filename }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Size</v-list-item-title>
          <v-list-item-subtitle>
            {{ $filters.filesize(file.size) }}
            <span v-if="state === 'updated'"
              >(new:
              {{ $filters.filesize(upload.files[file.path].size) }})</span
            >
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Last update</v-list-item-title>
          <v-list-item-subtitle
            >{{ $filters.datetime(file.mtime) }} ({{
              $filters.timediff(file.mtime)
            }})
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <!--     render only if file is smaller than 100MB-->
    <div class="container" v-if="mimetype && file.size < 104857600">
      <output>
        <!--      TODO: V3_UPGRADE temporary disabled - vue-pdf has issue with require function  -->
        <!--        <pdf-->
        <!--          :src="downloadLink"-->
        <!--          @num-pages="pageCount = $event"-->
        <!--          @page-loaded="currentPage = $event"-->
        <!--          v-if="mimetype.match('pdf')"-->
        <!--        ></pdf>-->
        <img :src="downloadLink" v-if="mimetype.match('image')" />
        <v-textarea
          v-else-if="mimetype.match('text')"
          :auto-grow="true"
          :readonly="true"
          :model-value="content"
          variant="solo-filled"
        >
        </v-textarea>
      </output>
    </div>
  </div>
</template>

<script lang="ts">
import Path from 'path'
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'
// import pdf from 'vue-pdf'
import { DownloadIcon, TrashIcon } from 'vue-tabler-icons'

import ActionButton from '@/common/components/ActionButton.vue'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'

const Colors = {
  added: 'green',
  removed: 'red',
  updated: 'orange'
}

export default defineComponent({
  name: 'FileInfoView',
  props: {
    namespace: String,
    projectName: String,
    location: {
      type: String,
      default: ''
    }
  },
  components: {
    // pdf,
    ActionButton,
    DownloadIcon,
    TrashIcon
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'uploads']),
    upload() {
      return this.uploads[this.project.path]
    },
    file() {
      if (!this.project.files[this.location]) {
        this.$router.replace({
          name: 'project',
          namespace: this.namespace,
          projectName: this.projectName
        })
      }
      return (
        this.project.files[this.location] || this.upload.files[this.location]
      )
    },
    filename() {
      return Path.basename(this.file.path)
    },
    downloadLink() {
      // added random number to request avoid to browser caching files
      return ProjectApi.constructDownloadProjectFileUrl(
        this.namespace,
        this.projectName,
        encodeURIComponent(this.file.path)
      )
    },
    state() {
      const diff = this.upload && this.upload.diff
      if (diff) {
        const path = this.file.path
        if (diff.added.includes(path)) {
          return 'added'
        } else if (diff.removed.includes(path)) {
          return 'removed'
        } else if (diff.updated.includes(path)) {
          return 'updated'
        }
      }
      return null
    },
    stateText() {
      return (
        {
          added: 'New file',
          removed: 'Deleted file',
          updated: 'Modified file'
        }[this.state] || this.state
      )
    },
    colors() {
      return Colors
    }
  },
  data() {
    return {
      previewUrl: '',
      pageCount: 0,
      currentPage: 0,
      content: null,
      mimetype: null
    }
  },
  created() {
    this.txtPreview()
  },
  methods: {
    ...mapActions(useProjectStore, ['deleteFiles']),
    txtPreview() {
      ProjectApi.getProjectFileByUrl(this.downloadLink).then((resp) => {
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
    }
  }
})
</script>

<style lang="scss" scoped>
.status {
  margin: 0.5em auto;
  padding: 0 1em;
  text-align: center;
  color: #fff;
  height: 2em;
  line-height: 2em;
}

.v-list {
  :deep(.v-list__tile) {
    font-size: 14px;
    color: #444;

    .v-list__tile__title {
      font-weight: 500;
    }
  }
}

output img {
  max-width: 100%;
}
</style>
