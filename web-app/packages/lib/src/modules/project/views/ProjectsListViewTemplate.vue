<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <app-container>
    <template v-if="!namespace">
      <app-section ground class="py-2">
        <!-- Title with buttons -->
        <header class="flex flex-wrap align-items-center">
          <h1 class="text-3xl font-semibold">
            {{ header }}
          </h1>
          <div class="flex flex-grow-1 align-items-center justify-content-end">
            <PButton
              v-if="canCreateProject && loggedUser && loggedUser.email"
              @click="newProjectDialog"
              data-cy="action-button-create"
              class="w-auto mr-1"
            >
              Create project
            </PButton>
            <PButton
              v-if="!onlyPublic && loggedUser && loggedUser.email"
              severity="secondary"
              @click="findPublicProjects"
              data-cy="action-button-public-projects"
              outlined
              rounded
              icon="ti ti-world text-xl"
            />
          </div>
        </header>
        <!-- Filters -->
        <div class="flex align-items-center justify-content-between">
          <span class="p-input-icon-left">
            <i class="ti ti-search text-xl"></i>
            <PInputText
              placeholder="Search projects by name"
              :pt="{ root: { class: 'border-round-xl' } }"
            />
          </span>
          <PButton
            severity="secondary"
            text
            icon="ti ti-settings"
            @click="toggleMenu"
            aria-haspopup="true"
            aria-controls="projects-filters-menu"
          />
          <PMenu
            ref="menu"
            id="projects-filters-menu"
            :model="filterMenuItems"
            :popup="true"
          />
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
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem } from 'primevue/menuitem'
import { defineComponent, ref } from 'vue'

import { AppContainer, AppSection } from '@/common'
import { useDialogStore } from '@/modules'
import { useLayoutStore } from '@/modules/layout/store'
import ProjectForm from '@/modules/project/components/ProjectForm.vue'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'ProjectsListView',
  components: { AppContainer, AppSection },
  props: {
    namespace: String,
    canCreateProject: Boolean
  },
  setup() {
    const menu = ref()

    return { menu }
  },
  computed: {
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useLayoutStore, ['drawer']),
    header() {
      return this.onlyPublic ? 'Mergin Maps public projects' : 'My projects'
    },
    onlyPublic() {
      return this.$route.name === 'explore' || !this.loggedUser?.email
    },
    filterMenuItems(): MenuItem[] {
      return [
      {
          label: 'Sort by name',
          command: () => {
            console.log('hhh')
          }
        },
        {
          label: 'Sort by last updated',
        },
        {
          label: 'Sort by file size'
        }
      ]
    }
  },
  methods: {
    ...mapActions(useDialogStore, ['show']),

    findPublicProjects() {
      this.$router.push({
        name: 'explore'
      })
    },
    newProjectDialog() {
      const dialog = { maxWidth: 500, persistent: true }
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
      this.$refs.menu.toggle(event)
    }
  }
})
</script>

<style lang="scss" scoped></style>
