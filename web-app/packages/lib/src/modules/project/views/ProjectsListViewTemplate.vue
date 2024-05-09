<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <app-container>
      <template v-if="!namespace">
        <app-section ground class="mb-3">
          <template #header>
            <h1 class="headline-h3">
              {{ header }}
              <span class="text-color-medium-green">({{ projectsCount }})</span>
            </h1>
          </template>
          <template #headerActions>
            <PButton
              v-if="canCreateProject && loggedUser && loggedUser.email"
              @click="newProjectDialog"
              data-cy="action-button-create"
              label="Create project"
            />
          </template>
          <div class="flex align-items-center justify-content-between mt-3">
            <span class="p-input-icon-left flex-grow-1">
              <i class="ti ti-search paragraph-p3"></i>
              <PInputText
                placeholder="Search projects by name"
                v-model="projectsStore.projectsSearch"
                class="w-full"
              />
            </span>
            <app-menu :items="filterMenuItems" />
          </div>
        </app-section>
        <app-section>
          <slot name="projects" :onlyPublic="onlyPublic"></slot>
        </app-section>
      </template>
      <!-- TODO: Do not understand logic here :() -->
      <AppSection v-else>
        <span>
          <b>Namespace not found</b><br />
          Please check if address is written correctly
        </span>
      </AppSection>
    </app-container>
    <community-banner v-if="!onlyPublic && loggedUser && loggedUser.email" />
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem, MenuItemCommandEvent } from 'primevue/menuitem'
import { defineComponent, ref } from 'vue'

import CommunityBanner from '../components/CommunityBanner.vue'

import { AppContainer, AppSection } from '@/common'
import AppMenu from '@/common/components/AppMenu.vue'
import { useDialogStore, useProjectStore } from '@/modules'
import { useLayoutStore } from '@/modules/layout/store'
import ProjectForm from '@/modules/project/components/ProjectForm.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProjectsListView',
  components: { AppContainer, AppSection, AppMenu, CommunityBanner },
  props: {
    namespace: String,
    canCreateProject: Boolean
  },
  setup() {
    const projectsStore = useProjectStore()
    const menu = ref()

    return { menu, projectsStore }
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useProjectStore, ['projectsSorting', 'projectsCount']),
    header() {
      return this.onlyPublic ? 'Public projects' : 'My projects'
    },
    onlyPublic() {
      return this.$route.name === 'explore' || !this.loggedUser?.email
    },
    filterMenuItems(): MenuItem[] {
      return [
        {
          label: 'Sort by name A-Z',
          key: 'name-asc',
          value: 'name',
          sortDesc: false
        },
        {
          label: 'Sort by name Z-A',
          key: 'name-desc',
          value: 'name',
          sortDesc: true
        },
        {
          label: 'Sort by last updated',
          key: 'updated',
          value: 'updated',
          sortDesc: true
        },
        {
          label: 'Sort by files size',
          key: 'meta.size',
          value: 'meta.size',
          sortDesc: true
        }
      ].map((item) => ({
        ...item,
        command: (e: MenuItemCommandEvent) => this.menuItemClick(e),
        class:
          this.projectsSorting.sortBy === item.value &&
          this.projectsSorting.sortDesc === item.sortDesc
            ? 'bg-primary-400'
            : ''
      }))
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['show']),
    ...mapActions(useProjectStore, ['setProjectsSorting']),

    newProjectDialog() {
      const dialog = { persistent: true, header: 'New project' }
      this.show({
        component: ProjectForm,
        params: {
          listeners: {
            error: (err, data) => this.$emit('new-project-error', err, data)
          },
          dialog
        }
      })
    },
    toggleMenu(event) {
      const menu = this.$refs.menu as { toggle: (event: Event) => void }
      menu.toggle(event)
    },
    menuItemClick(e: MenuItemCommandEvent) {
      this.setProjectsSorting({
        sortBy: e.item.value,
        sortDesc: e.item.sortDesc
      })
    }
  }
})
</script>

<style lang="scss" scoped></style>
