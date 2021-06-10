# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-card>
    <v-toolbar dense text dark color="primary">
      <v-toolbar-title>Data Sync</v-toolbar-title>
      <v-spacer/>
      <v-btn icon @click="resetUpload">
        <v-icon>close</v-icon>
      </v-btn>
    </v-toolbar>

    <v-card-text v-if="upload.diff && upload.diff.changes">
      <v-layout class="stats-line">
        <label>Removed files:</label>
        <v-spacer/>
        <span class="red--text">{{ upload.diff.removed.length }}</span>
        <v-icon small color="red">delete</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Added files:</label>
        <v-spacer/>
        <span class="green--text">{{ upload.diff.added.length }}</span>
        <v-icon small color="green">add_circle</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Modified files:</label>
        <v-spacer/>
        <span class="orange--text">{{ upload.diff.updated.length }}</span>
        <v-icon small color="orange">edit</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Renamed files:</label>
        <v-spacer/>
        <span class="grey--text">{{ upload.diff.moved.length }}</span>
        <v-icon small color="grey">shuffle</v-icon>
      </v-layout>
      <v-layout class="stats-line">
        <label>Upload data size:</label>
        <v-spacer/>
        <span>{{ uploadSize | filesize }}</span>
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
        <v-spacer/>
        <span style="padding-right: 30px;">Remaining files: {{ remainingAnalyzingFiles }}</span>
      </v-layout>
    </v-card-text>

    <v-card-actions v-if="upload.diff && upload.diff.changes">
      <v-spacer/>
      <v-btn
        id="update-files-btn"
        @click="confirmUpload"
        :disabled="upload.running || remainingAnalyzingFiles > 0"
      >
        <v-icon class="mr-2">cloud_upload</v-icon>
        Update
      </v-btn>
      <v-spacer/>
    </v-card-actions>

  </v-card>
</template>

<script>
import { mapState } from 'vuex'
import pick from 'lodash/pick'
import axios from 'axios'
import { waitCursor } from '../util'
import { isVersionedFile, CHUNK_SIZE } from '../mergin'
import MerginAPIMixin from '@/mixins/MerginAPI'
import OrganisationsMixin from '@/mixins/Organisation'


export default {
  data () {
    return {
      source: null
    }
  },
  props: {
    namespace: String
  },
  mixins: [MerginAPIMixin, OrganisationsMixin],
  computed: {
    ...mapState(['project', 'uploads', 'app']),
    upload () {
      return this.uploads[this.project.path]
    },
    uploadSize () {
      if (this.upload) {
        const { added, updated } = this.upload.diff
        return added.concat(updated).reduce((sum, path) => {
          return sum + this.upload.files[path].size
        }, 0)
      }
      return 0
    },
    remainingAnalyzingFiles () {
      const list = (this.upload && this.upload.analysingFiles) || []
      return list.length
    }
  },
  methods: {
    resetUpload () {
      this.$store.commit('discardUpload', this.project.path)
      if (this.source) {
        this.source.cancel('Operation canceled by the user.')
        delete this.source
      }
    },
    async uploadChanges () {
      const { added, removed, updated, moved } = this.upload.diff
      const fileInfoFields = ['path', 'checksum', 'size', 'mtime', 'chunks']
      const changes = {
        removed: removed.map(path => pick(this.project.files[path], fileInfoFields)),
        added: added.map(path => pick(this.upload.files[path], fileInfoFields)),
        updated: updated.map(path => pick(this.upload.files[path], fileInfoFields)),
        renamed: moved
      }

      const projectPath = this.project.path
      const version = this.project.version || 'v0'
      let resp
      try {
        resp = await this.$http.post(`/v1/project/push/${projectPath}`, { version: version, changes })
      } catch (err) {
        const msg = (err.response && err.response.data.detail) || 'Error'
        this.$notification.error(msg)
        return
      }
      const { transaction } = resp.data
      if (!transaction) {
        this.$store.commit('discardUpload', projectPath)
        this.$notification.show('Project updated')
        this.$store.commit('project', resp.data)
        return
      }

      this.source = axios.CancelToken.source()
      const promises = []
      added.concat(updated).forEach(path => {
        this.upload.files[path].chunks.forEach((chunk, index) => {
          const file = this.upload.files[path].file
          const offset = index * CHUNK_SIZE
          const data = file.slice(offset, offset + CHUNK_SIZE)
          const p = new Promise((resolve) => {
            const p = this.$http.post(`/v1/project/push/chunk/${transaction}/${chunk}`, data, { cancelToken: this.source.token, 'axios-retry': { retries: 5 } })
            p.then(() => {
              // attach commits to upload object to monitor progress
              this.$store.commit('chunkUploaded', projectPath)
            }).catch(() => {})
            resolve(p)
          })
          promises.push(p)
        })
      })

      // fire up chunks uploads
      this.$store.commit('startUpload')
      Promise.all(promises)
        .then(() => {
          // call server to finish upload transaction
          this.$http.post(`/v1/project/push/finish/${transaction}`, { cancelToken: this.source.token, 'axios-retry': { retries: 5 } }).then(resp => {
            this.$store.commit('discardUpload', projectPath)
            this.$notification.show(`Upload finished: ${projectPath}`)
            this.$store.commit('project', resp.data)
            if (this.namespace in this.app.user.profile.organisations) {
              this.getOrganisation(this.namespace)
            } else {
              this.fetchUserProfile(this.app.user.username)
            }
            waitCursor(false)
          }).catch(err => {
            this.$store.commit('cancelUpload', projectPath)
            const msg = (err.__CANCEL__) ? err.message : (err.response && err.response.data.detail) || 'Error'
            this.$notification.error(msg)
            this.$http.post(`/v1/project/push/cancel/${transaction}`)
            waitCursor(false)
          })
        })
        .catch(err => {
          this.$store.commit('cancelUpload', projectPath)
          const msg = (err.__CANCEL__) ? err.message : (err.response && err.response.data.detail) || 'Error'
          this.$notification.error(msg)
          this.$http.post(`/v1/project/push/cancel/${transaction}`)
          waitCursor(false)
        })
    },
    confirmUpload () {
      const props = {
        text: 'This update contains also changes in versioned files whose history will be lost. Are you sure to update project?',
        confirmText: 'Update'
      }
      const listeners = {
        confirm: () => this.uploadChanges()
      }

      if (this.upload.diff.updated.filter(i => isVersionedFile(i)).length) {
        this.$dialog.prompt({ props, listeners, dialog: { maxWidth: 500 } })
      } else {
        this.uploadChanges()
      }
    }
  }
}
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
