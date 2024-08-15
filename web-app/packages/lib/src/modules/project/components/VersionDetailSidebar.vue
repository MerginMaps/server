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
          <dt class="paragraph-p6 opacity-80 mb-2">Version</dt>
          <dl>
            <h3 class="headline-h3 mt-0">
              {{ version.name }}
            </h3>
          </dl>
        </div>
        <PDivider class="m-0" />
        <div class="col-6">
          <dt class="paragraph-p6 opacity-80 mb-2">Author</dt>
          <dl class="font-semibold paragraph-p5">
            {{ version.author }}
          </dl>
        </div>
        <div class="col-6 flex flex-column align-items-end">
          <dt class="paragraph-p6 opacity-80 mb-2">Project size</dt>
          <dl class="font-semibold paragraph-p5">
            {{ $filters.filesize(version.project_size) }}
          </dl>
        </div>
        <div class="col-12">
          <dt class="paragraph-p6 opacity-80 mb-2">Created</dt>
          <dl class="font-semibold paragraph-p5">
            {{ $filters.datetime(version.created) }}
          </dl>
        </div>
        <div class="col-12">
          <dt class="paragraph-p6 opacity-80 mb-2">User agent</dt>
          <dl class="font-semibold paragraph-p5">
            {{ version.user_agent }}
          </dl>
        </div>
      </dl>
      <PAccordion
        multiple
        collapse-icon="ti ti-chevron-right"
        expand-icon="ti ti-chevron-down"
        :active-index="activeAccordionItems"
        :pt="{
          accordiontab: {
            headerAction: {
              class: 'surface-section border-x-none border-noround p-2'
            },
            content: {
              class: 'border-none'
            }
          }
        }"
      >
        <PAccordionTab
          v-for="item in changeTabs"
          :key="item.key"
          :disabled="!changes[item.key].length"
        >
          <template #header>
            <app-circle :severity="item.severity" class="mr-2">
              <i :class="['ti', `${item.icon}`]"></i>
            </app-circle>
            <span class="paragraph-p5 opacity-80">{{ item.text }}</span>
            <app-circle class="ml-auto">
              {{ changes[item.key].length }}
            </app-circle></template
          >
          <div
            v-for="change in changes[item.key]"
            :key="change.path"
            class="py-2 paragraph-p6"
          >
            <div class="flex align-items-center justify-content-between mb-2">
              <span class="w-10 font-semibold">{{ change.path }}</span>
              <span class="flex-shrink-0">{{
                $filters.filesize(
                  version.changesets[change.path]
                    ? version.changesets[change.path]['size']
                    : change.size
                )
              }}</span>
            </div>
            <template
              v-if="
                version.changesets[change.path] &&
                !version.changesets[change.path].error
              "
              ><router-link
                class="text-color-forest text-underline font-semibold"
                :to="{
                  name: 'file-version-detail',
                  params: {
                    namespace: version.namespace,
                    projectName: version.project_name,
                    version_id: version.name,
                    path: change.path
                  }
                }"
                >Show advanced</router-link
              >
              <file-changeset-summary-table
                :changesets="version.changesets[change.path]['summary']"
              />
            </template>
            <div
              v-else-if="
                version.changesets[change.path] &&
                version.changesets[change.path].error
              "
              class="text-center"
            >
              Details not available:
              {{ version.changesets[change.path].error }}
            </div>
          </div>
        </PAccordionTab>
      </PAccordion>
    </app-sidebar-right>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import AppCircle from '@/common/components/AppCircle.vue'
import AppSidebarRight from '@/common/components/AppSidebarRight.vue'
import { getErrorMessage } from '@/common/error_utils'
import { ProjectVersion } from '@/modules'
import { useNotificationStore } from '@/modules/notification/store'
import FileChangesetSummaryTable from '@/modules/project/components/FileChangesetSummaryTable.vue'
import { ProjectApi } from '@/modules/project/projectApi'
import { useProjectStore } from '@/modules/project/store'

export default defineComponent({
  name: 'VersionDetailView',
  components: { FileChangesetSummaryTable, AppSidebarRight, AppCircle },
  props: {
    asAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      version: null as ProjectVersion
    }
  },
  computed: {
    ...mapState(useProjectStore, ['project', 'versions']),
    changeTabs(): {
      key: 'added' | 'updated' | 'removed'
      severity: 'success' | 'warn' | 'danger'
      text: string
      icon: string
    }[] {
      return [
        {
          key: 'added',
          severity: 'success',
          text: 'Files added',
          icon: 'ti-plus'
        },
        {
          key: 'updated',
          severity: 'warn',
          text: 'Files edited',
          icon: 'ti-pencil'
        },
        {
          key: 'removed',
          severity: 'danger',
          text: 'Files removed',
          icon: 'ti-trash'
        }
      ]
    },
    changes() {
      return this.version?.changes
    },
    changesets() {
      return this.version?.changesets
    },
    activeAccordionItems(): number[] {
      return this.changeTabs.reduce<number[]>((acc, tab, index) => {
        if (this.changes[tab.key].length > 0) {
          acc.push(index)
        }
        return acc
      }, [])
    },
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
