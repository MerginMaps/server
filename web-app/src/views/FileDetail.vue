# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <div>
    <div
      v-if="state"
      v-text="stateText"
      :class="['status', colors[state]]"
    />
    <v-btn v-if="project.permissions.upload && this.state !== 'removed'"
           @click="removeSelected"
           style="background-color: #f44336; float: right; color: white">
      <v-icon>delete</v-icon>
        Remove file
    </v-btn>
    <v-btn
          :disabled="state === 'added'"
          :href="downloadLink"
          style="float: right;">
          <v-icon>get_app</v-icon>
          Download File
        </v-btn>

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
            {{ file.size | filesize }}
            <span v-if="state === 'updated'">(new: {{ upload.files[file.path].size | filesize }})</span>
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Last update</v-list-item-title>
          <v-list-item-subtitle>{{ file.mtime | datetime }} ({{ file.mtime | timediff }})</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <!--     render only if file is smaller than 100MB-->
     <div class="container" v-if="mimetype && file.size < 104857600">
       <output>
         <pdf
            :src="downloadLink"
            @num-pages="pageCount = $event"
            @page-loaded="currentPage = $event"
            v-if="mimetype.match('pdf')"
        ></pdf>
      <img :src="downloadLink" v-else-if="mimetype.match('image')">
      <v-textarea
              v-else-if="mimetype.match('text')"
             :auto-grow="true"
             :readonly="true"
             :value="content"
             :box="true"
             solo
          >
      </v-textarea>
    </output>
  </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import Path from 'path'
import pdf from 'vue-pdf'

const Colors = {
  added: 'green',
  removed: 'red',
  updated: 'orange',
  rmoved: 'red',
  nmoved: 'green'
}

export default {
  name: 'file-info',
  props: {
    namespace: String,
    projectName: String,
    location: {
      type: String,
      default: ''
    }
  },
  components: {
    pdf
  },
  computed: {
    ...mapState(['project', 'uploads']),
    upload () {
      return this.uploads[this.project.path]
    },
    file () {
      if (!this.project.files[this.location]) {
        this.$router.replace({ name: 'project', namespace: this.namespace, projectName: this.projectName })
      }
      return this.project.files[this.location] || this.upload.files[this.location]
    },
    filename () {
      return Path.basename(this.file.path)
    },
    downloadLink () {
      // added random number to request avoid to browser caching files
      return this.$http.absUrl(`/v1/project/raw/${this.namespace}/${this.projectName}?file=${encodeURIComponent(this.file.path)}&random=${Math.random()}`)
    },
    state () {
      const diff = this.upload && this.upload.diff
      if (diff) {
        const path = this.file.path
        if (diff.added.includes(path)) {
          return 'added'
        } else if (diff.removed.includes(path)) {
          return 'removed'
        } else if (diff.updated.includes(path)) {
          return 'updated'
        } else if (diff.moved.find(f => f.path === path)) {
          return 'rmoved'
        } else if (diff.moved.find(f => f.new_path === path)) {
          return 'nmoved'
        }
      }
      return null
    },
    stateText () {
      return {
        added: 'New file',
        removed: 'Deleted file',
        updated: 'Modified file'
      }[this.state] || this.state
    },
    colors () {
      return Colors
    }
  },
  data () {
    return {
      previewUrl: '',
      pageCount: 0,
      currentPage: 0,
      content: null,
      mimetype: null
    }
  },
  created () {
    this.txtPreview()
  },
  methods: {
    txtPreview () {
      this.$http.get(this.downloadLink)
        .then(resp => {
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
    removeSelected () {
      this.$store.commit('deleteFiles', [this.file.path])
    }
  }
}
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
  ::v-deep .v-list__tile {
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
