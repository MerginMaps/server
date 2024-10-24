<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div v-if="version">
    <app-sidebar-right v-model="sidebarVisible" data-cy="app-right-sidebar">
      <template #title>{{ queryId }}</template>
      <template #headerButtons
        ><PButton
          type="button"
          @click="downloadVersion"
          icon="ti ti-download"
          text
          rounded
          plain
          class="p-1 text-2xl"
          data-cy="file-detail-download-btn"
        ></PButton
      ></template>
      <dl class="grid grid-nogutter row-gap-4">
        <div class="col-12">
          <dt class="paragraph-p6 opacity-80">Version</dt>
          <dd>
            <h3 class="headline-h3 mt-0">
              {{ version.name }}
            </h3>
          </dd>
        </div>
        <PDivider class="m-0" />
        <div class="col-6">
          <dt class="paragraph-p6 opacity-80">Author</dt>
          <dd class="font-semibold paragraph-p5">
            {{ version.author }}
          </dd>
        </div>
        <div class="col-6 flex flex-column align-items-end">
          <dt class="paragraph-p6 opacity-80">Project size</dt>
          <dd class="font-semibold paragraph-p5">
            {{ $filters.filesize(version.project_size) }}
          </dd>
        </div>
        <div class="col-12">
          <dt class="paragraph-p6 opacity-80">Created</dt>
          <dd class="font-semibold paragraph-p5">
            {{ $filters.datetime(version.created) }}
          </dd>
        </div>
        <div class="col-12">
          <dt class="paragraph-p6 opacity-80">User agent</dt>
          <dd class="font-semibold paragraph-p5">
            {{ version.user_agent }}
          </dd>
        </div>
      </dl>
      <project-version-changes v-if="version" :version="version" />
    </app-sidebar-right>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import ProjectVersionChanges from './ProjectVersionChanges.vue'

import AppSidebarRight from '@/common/components/AppSidebarRight.vue'
import { getErrorMessage } from '@/common/error_utils'
import { ProjectVersion } from '@/modules'
import { useNotificationStore } from '@/modules/notification/store'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'VersionDetailSidebar',
  components: { AppSidebarRight, ProjectVersionChanges },
  data() {
    return {
      version: null as ProjectVersion
    }
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'versions']),
    downloadUrl() {
      return ProjectApi.constructDownloadProjectVersionUrl(
        this.project.namespace,
        this.project.name,
        this.queryId
      )
    },
    queryId(): string {
      return this.$route.query.version_id as string
    },
    sidebarVisible: {
      get() {
        return !!this.queryId
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
  watch: {
    queryId: {
      immediate: true,
      handler() {
        if (this.queryId) {
          this.getVersion()
          return
        }
        this.sidebarVisible = false
      }
    }
  },
  methods: {
    ...mapActions(useNotificationStore, ['error']),
    async getVersion() {
      try {
        const response = await ProjectApi.getProjectVersion(
          this.project.id,
          this.queryId
        )
        this.version = response.data
      } catch (err) {
        this.error({
          text: getErrorMessage(err, 'Failed to fetch project version')
        })
      }
    },
    downloadVersion() {
      window.location.href = this.downloadUrl
    }
  }
})
</script>

<style lang="scss" scoped></style>
