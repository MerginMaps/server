<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PMenubar
    class="app-header p-2"
    :pt="{
      start: {
        class: 'w-10'
      },
      end: {
        class: 'align-self-start lg:align-self-center flex-wrap'
      }
    }"
  >
    <template #start
      ><slot name="menu">
        <div
          class="flex flex-column lg:flex-row align-items-start lg:align-items-center"
        >
          <PButton
            class="mr-2"
            :icon="menuButtonIcon"
            plain
            text
            rounded
            @click="setDrawer({ drawer: !drawer })"
            :pt="{ icon: { class: 'text-3xl' } }"
          />
          <app-breadcrumbs></app-breadcrumbs>
        </div>
      </slot>
    </template>

    <template #end>
      <div class="flex align-items-center">
        <slot name="invitationsIcon"></slot>
        <PButton
          text
          plain
          aria-haspopup="true"
          aria-controls="app-header-profile"
          data-cy="app-header-profile-btn"
          @click="toggleMenu"
          class="p-2 shadow-none"
        >
          <div class="mr-2 max-w-80 flex flex-column align-items-start">
            <span :style="{ whiteSpace: 'nowrap' }">{{ userName }}</span>
            <span v-if="renderNamespace" class="font-normal">
              {{ currentNamespace || 'no workspace' }}
            </span>
          </div>
          <i class="ti ti-chevron-down"></i
        ></PButton>
        <POverlayPanel
          id="app-header-profile"
          data-cy="app-header-profile"
          ref="menu"
          :pt="{ root: { class: 'p-3' }, content: { class: 'p-0' } }"
        >
          <div class="flex align-items-center mb-2">
            <PAvatar
              :label="avatarLabel"
              size="xlarge"
              shape="circle"
              :pt="{
                root: {
                  class: 'mr-2 text-color-forest font-semibold',
                  style: {
                    borderRadius: '50%'
                  }
                }
              }"
            />
            <div>
              <p class="font-semibold text-sm">{{ getUserFullName }}</p>
              <p class="text-sm">{{ loggedUser.email }}</p>
            </div>
          </div>
          <slot></slot>
          <PMenu
            :model="[...(menuItems ?? []), ...profileMenuItems]"
            :pt="{
              root: { style: { width: '100%' }, class: 'border-none' },
              label: { class: 'font-semibold' },
              icon: { class: 'text-color text-2xl' },
              action: { class: 'flex align-items-center' }
            }"
          ></PMenu>
        </POverlayPanel>
        <AppMenu :items="_helpMenuItems" :icon="'ti ti-help'" />
      </div>
    </template>
  </PMenubar>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem } from 'primevue/menuitem'
import { defineComponent, ref, PropType } from 'vue'

import { AppBreadcrumbs } from '.'

import { AppMenu, useInstanceStore } from '@/main'
import { useLayoutStore } from '@/modules/layout/store'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'app-header-template',
  components: {
    AppBreadcrumbs,
    AppMenu
  },
  props: {
    renderNamespace: {
      type: Boolean,
      default: false
    },
    menuItems: {
      type: Array as PropType<MenuItem[]>
    },
    helpMenuItems: {
      type: Array as PropType<MenuItem[]>
    }
  },
  setup() {
    const menu = ref()

    const toggleMenu = (event) => {
      menu.value.toggle(event)
    }

    return {
      menu,
      toggleMenu
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    ...mapState(useLayoutStore, ['drawer', 'isUnderOverlayBreakpoint']),
    ...mapState(useUserStore, ['loggedUser', 'getUserFullName']),
    ...mapState(useProjectStore, ['currentNamespace']),
    profileMenuItems() {
      return [
        {
          label: 'Your profile',
          icon: 'ti ti-user-circle',
          command: () => {
            this.$router.push({
              name: 'user_profile',
              username: this.loggedUser?.username
            })
          }
        },
        {
          label: 'Sign out',
          icon: 'ti ti-logout',
          command: () => {
            this.logout()
          }
        }
      ] as MenuItem[]
    },
    _helpMenuItems() {
      return [
        {
          label: 'Documentation',
          url: this.configData?.docs_url
        },
        {
          label: 'Community chat',
          url: import.meta.env.VITE_VUE_APP_JOIN_COMMUNITY_LINK
        },
        ...(this.helpMenuItems ?? [])
      ].map((item) => ({ ...item, class: 'font-semibold p-1' })) as MenuItem[]
    },
    avatarLabel() {
      return this.loggedUser?.username?.charAt(0).toUpperCase()
    },
    userName() {
      return this.getUserFullName.length > 15
        ? `${this.getUserFullName.substring(0, 15)}...`
        : this.getUserFullName
    },
    menuButtonIcon() {
      if (this.isUnderOverlayBreakpoint) {
        return 'ti ti-menu-2'
      }

      return this.drawer
        ? 'ti ti-layout-sidebar-left-collapse'
        : 'ti ti-layout-sidebar-left-expand'
    }
  },
  methods: {
    ...mapActions(useLayoutStore, ['setDrawer']),
    ...mapActions(useUserStore, { logoutUser: 'logout' }),

    async logout() {
      try {
        await this.logoutUser()
        if (this.$route.path === '/') {
          location.reload()
        } else {
          location.href = '/'
        }
      } catch (e) {
        console.error(e)
      }
    }
  }
})
</script>

<style lang="scss" scoped></style>
