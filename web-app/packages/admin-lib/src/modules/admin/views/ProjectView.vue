<template>
  <admin-layout>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">Project details</h1>
        </template>
      </app-section>
    </app-container>

    <app-container>
      <app-section class="p-4">
        <div class="flex flex-column row-gap-3">
          <h2 class="headline-h2" data-cy="project-name">
            {{ project?.name }}
          </h2>
          <dl
            class="project-view-detail-list paragraph-p5 flex flex-column gap-3"
          >
            <div>
              <dt class="paragraph-p6 opacity-80">Created</dt>
              <dd class="font-semibold" data-cy="project-owner">
                {{ $filters.date(project?.created) }}
              </dd>
            </div>
            <div>
              <dt class="paragraph-p6 opacity-80">Updated</dt>
              <dd class="font-semibold" data-cy="project-created">
                {{ $filters.date(project?.updated) }}
              </dd>
            </div>
            <div>
              <dt class="paragraph-p6 opacity-80">Disk usage</dt>
              <dd class="font-semibold" data-cy="project-created">
                {{ $filters.filesize(project?.disk_usage, 'MB') }}
              </dd>
            </div>
          </dl>
        </div>
      </app-section>
    </app-container>

    <app-container>
      <app-section>
        <template #title>Advanced</template>
        <div class="flex flex-column row-gap-3 paragraph-p5 px-4 pb-4">
          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
          >
            <div class="flex-grow-1">
              <template v-if="project?.access?.public">
                <p class="title-t3">Public project</p>
                <span class="paragraph-p6 opacity-80"
                  >The project will be visible to everyone if it is marked as
                  public.</span
                >
              </template>
              <template v-else>
                <p class="title-t3">This is private project</p>
                <span class="paragraph-p6 opacity-80"
                  >Make this project visible to anyone.</span
                >
              </template>
            </div>
            <div class="flex-shrink-0">
              <i v-if="project?.access?.public" class="ti ti-check" />
              <i v-else class="ti ti-x" />
            </div>
          </div>

          <div
            :class="[
              'flex flex-column align-items-start',
              'row-gap-2',
              'md:align-items-center md:flex-row'
            ]"
          >
            <div class="flex-grow-1">
              <p class="title-t3">Delete project</p>
              <span class="paragraph-p6 opacity-80"
                >Deleting this project will remove it and all its data. This
                action cannot be undone.</span
              >
            </div>
            <div class="flex-shrink-0">
              <PButton
                @click="confirmDelete"
                severity="danger"
                data-cy="project-delete-btn"
                label="Delete project"
              />
            </div>
          </div>
        </div>
      </app-section>
    </app-container>
  </admin-layout>
</template>

<script setup lang="ts">
import {
  ConfirmDialog,
  useDialogStore,
  AppSection,
  AppContainer,
  ConfirmDialogProps,
  useProjectStore
} from '@mergin/lib'
import { computed, watch, defineProps } from 'vue'
import { useRoute } from 'vue-router'

import { useAdminStore } from '@/modules'
import AdminLayout from '@/modules/admin/components/AdminLayout.vue'

const route = useRoute()
const projectStore = useProjectStore()
const dialogStore = useDialogStore()
const adminStore = useAdminStore()

defineProps<{
  projectName: string
  namespace: string
}>()

const project = computed(() => projectStore.project)
const routeProjectName = computed(() => route?.params?.projectName as string)
const routeWorkspaceName = computed(() => route?.params?.namespace as string)

const fetchProject = (projectName: string, workspaceName: string) => {
  projectStore.project = null
  projectStore.fetchProject({
    namespace: workspaceName,
    projectName
  })
}

watch(
  [routeProjectName, routeWorkspaceName],
  ([projectName, workspaceName]) => {
    if (projectName && workspaceName) {
      fetchProject(projectName, workspaceName)
    }
  },
  { immediate: true }
)

const confirmDelete = () => {
  const props: ConfirmDialogProps = {
    text: `Are you sure you want to permanently delete this project?`,
    description: `Deleting this project will remove it
      and all its data. This action cannot be undone. Type in project name to confirm:`,
    hint: project.value.name,
    confirmText: 'Delete permanently',
    confirmField: {
      label: 'Project name',
      expected: project.value.name
    },
    severity: 'danger'
  }
  const listeners = {
    confirm: async () =>
      await adminStore.deleteProject({ projectId: project.value.id })
  }
  dialogStore.show({
    component: ConfirmDialog,
    params: { props, listeners, dialog: { header: 'Delete project' } }
  })
}
</script>

<style lang="scss" scoped>
.project-view-detail-list {
  max-width: 640px;
  width: 100%;
}
</style>
