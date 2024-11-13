<template>
  <admin-layout>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">Project version</h1>
        </template>
        <template #headerActions>
          <PButton
            severity="secondary"
            @click="download"
            label="Download"
            icon="ti ti-download"
          />
        </template>
      </app-section>
    </app-container>

    <app-container>
      <app-section class="p-4">
        <div class="flex flex-column row-gap-3">
          <h2 class="headline-h2" data-cy="project-name">
            <router-link
              :to="{
                name: AdminRoutes.PROJECT,
                params: {
                  namespace: project?.namespace,
                  projectName: project?.name
                }
              }"
              >{{ project?.name }}</router-link
            >
            / {{ data?.name }}
          </h2>
          <dl class="paragraph-p5 flex flex-column gap-3">
            <div>
              <dt class="paragraph-p6 opacity-80">Author</dt>
              <dd class="font-semibold">
                {{ data?.author }}
              </dd>
            </div>
            <div>
              <dt class="paragraph-p6 opacity-80">Project size</dt>
              <dd class="font-semibold">
                {{ $filters.filesize(data?.project_size) }}
              </dd>
            </div>
            <div>
              <dt class="paragraph-p6 opacity-80">Created</dt>
              <dd class="font-semibold">
                {{ $filters.datetime(data?.created) }}
              </dd>
            </div>
            <div>
              <dt class="paragraph-p6 opacity-80">User agent</dt>
              <dd class="font-semibold">
                {{ data?.user_agent }}
              </dd>
            </div>
          </dl>
        </div>
        <project-version-changes v-if="data" :version="data" />
      </app-section>
    </app-container>
  </admin-layout>
</template>

<script setup lang="ts">
import {
  AppContainer,
  AppSection,
  ProjectApi,
  useProjectStore,
  useNotificationStore,
  ProjectVersion,
  errorUtils,
  ProjectVersionChanges
} from '@mergin/lib'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { AdminRoutes } from '../routes'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

defineProps<{
  projectName?: string
  namespace?: string
  version_id?: string
}>()

const route = useRoute()
const projectStore = useProjectStore()
const notificationStore = useNotificationStore()
const data = ref<ProjectVersion>(null)
const project = computed(() => projectStore.project)
const versionId = computed(() => route.params.version_id as string)
const routeProjectName = computed(() => route?.params?.projectName as string)
const routeWorkspaceName = computed(() => route?.params?.namespace as string)

const fetchProject = async (projectName: string, workspaceName: string) => {
  projectStore.project = null
  await projectStore.fetchProject({
    namespace: workspaceName,
    projectName
  })
}

async function fetchVersion() {
  try {
    const response = await ProjectApi.getProjectVersion(
      project.value?.id,
      versionId.value
    )
    data.value = response.data
  } catch (err) {
    console.error(err)
    notificationStore.error({
      text: errorUtils.getErrorMessage(err, 'Failed to fetch project version')
    })
  }
}

watch(
  [routeProjectName, routeWorkspaceName, versionId],
  async ([projectName, workspaceName, versionId]) => {
    if (projectName && workspaceName && versionId) {
      await fetchProject(projectName, workspaceName)
      await fetchVersion()
    }
  },
  { immediate: true }
)

function download() {
  const url = ProjectApi.constructDownloadProjectVersionUrl(
    project.value?.namespace,
    project.value?.name,
    versionId.value
  )
  window.location.href = url
}
</script>
