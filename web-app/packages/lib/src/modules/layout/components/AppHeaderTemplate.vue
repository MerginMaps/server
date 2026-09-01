<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <PMenubar
      class="app-header"
      :pt="{
        menu: 'justify-content-between',
        start: {
          class: 'w-7'
        },
        end: {
          class: 'align-self-start lg:align-self-center flex-shrink-0'
        }
      }"
    >
      <template #start
        ><slot name="menu">
          <div class="flex flex-column lg:flex-row lg:align-items-center gap-2">
            <PButton
              v-if="hasSidebar"
              :icon="menuButtonIcon"
              plain
              text
              rounded
              @click="setDrawer({ drawer: !drawer })"
              :pt="{ icon: { class: 'text-3xl' } }"
            />
            <!-- Show inline with collapse / menu button only on large screens -->
            <app-breadcrumbs class="hidden lg:flex"></app-breadcrumbs>
          </div>
        </slot>
      </template>

      <template #end>
        <div class="flex align-items-center flex-shrink-0">
          <slot name="action-button"></slot>
          <slot
            v-if="loggedUser"
            name="profile-button"
            :toggle-menu="toggleMenu"
            :logged-user="loggedUser"
            :menu-visible="menuVisible"
          >
            <PButton
              text
              plain
              aria-haspopup="true"
              aria-controls="app-header-profile"
              data-cy="app-header-profile-btn"
              @click="toggleMenu"
              class="p-2 shadow-none"
            >
              <slot name="invitationsIcon"></slot>
              <div class="mr-2 max-w-80 flex flex-column align-items-end">
                <span class="title-t4" :style="{ whiteSpace: 'nowrap' }">{{
                  userName
                }}</span>
                <span
                  v-if="renderNamespace"
                  class="paragraph-p6 opacity-80 font-normal"
                >
                  {{ currentWorkspace?.name || 'no workspace' }}
                </span>
              </div>
              <i
                :class="menuVisible ? 'ti ti-chevron-up' : 'ti ti-chevron-down'"
              ></i>
            </PButton>
          </slot>
          <PButton
            v-else
            text
            plain
            aria-haspopup="true"
            aria-controls="app-header-profile"
            data-cy="app-header-profile-btn"
            @click="login"
            class="p-2 shadow-none"
            label="Sign in"
          />
          <POverlayPanel
            v-if="loggedUser"
            id="app-header-profile"
            data-cy="app-header-profile"
            ref="menu"
            @show="menuVisible = true"
            @hide="menuVisible = false"
            :pt="{ root: { class: 'p-3' }, content: { class: 'p-0' } }"
          >
            <div class="flex align-items-center mb-3">
              <PAvatar
                :label="$filters.getAvatar(loggedUser.email, loggedUser.name)"
                size="large"
                shape="circle"
                :pt="{
                  root: {
                    class: 'mr-2 font-semibold flex-shrink-0',
                    style: {
                      borderRadius: '50%'
                    }
                  }
                }"
              />
              <div class="flex flex-column">
                <p class="title-t4 overflow-wrap-anywhere">
                  {{ getUserFullName }}
                </p>
                <p class="paragraph-p6 overflow-wrap-anywhere">
                  {{ loggedUser.email }}
                </p>
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
          <PButton
            text
            plain
            rounded
            icon="ti ti-help"
            @click="toggleMenuHelp"
            aria-haspopup="true"
            aria-controls="menu-help"
            class="paragraph-p4 text-color hidden md:inline-flex"
          />
          <PMenu
            ref="menuHelp"
            id="menu-help"
            :model="_helpMenuItems"
            :popup="true"
          />
        </div>
      </template>
    </PMenubar>
    <!-- Show breadcrumps under menu in smaller screens (only when the default menu slot is used) -->
    <app-breadcrumbs
      v-if="!$slots.menu"
      class="lg:hidden px-3 pb-3 pt-0"
    ></app-breadcrumbs>
  </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem } from 'primevue/menuitem'
import { defineComponent, ref, PropType } from 'vue'

import { AppBreadcrumbs } from '.'

import { UserRouteName, useInstanceStore } from '@/main'
import { useLayoutStore } from '@/modules/layout/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'app-header-template',
  components: {
    AppBreadcrumbs
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
    const menuHelp = ref()
    const menuVisible = ref(false)

    const toggleMenu = (event) => {
      menu.value.toggle(event)
    }

    const toggleMenuHelp = (event) => {
      menuHelp.value.toggle(event)
    }

    return {
      menu,
      menuHelp,
      menuVisible,
      toggleMenu,
      toggleMenuHelp
    }
  },
  computed: {
    ...mapState(useInstanceStore, ['configData']),
    ...mapState(useLayoutStore, ['drawer', 'isUnderOverlayBreakpoint']),
    ...mapState(useUserStore, [
      'loggedUser',
      'getUserFullName',
      'currentWorkspace'
    ]),
    profileMenuItems() {
      return [
        ...(this.$router.hasRoute(UserRouteName.UserProfile)
          ? [
              {
                label: 'Your profile',
                icon: 'ti ti-user-circle',
                command: () => {
                  this.$router.push({
                    name: UserRouteName.UserProfile
                  })
                }
              }
            ]
          : []),
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
          url: this.configData?.docs_url,
          target: '_blank'
        },
        {
          label: 'Community',
          url: import.meta.env.VITE_VUE_APP_COMMUNITY_LINK,
          target: '_blank'
        },
        ...(this.helpMenuItems ?? [])
      ].map((item) => ({ ...item, class: 'font-semibold p-1' })) as MenuItem[]
    },
    userName() {
      return this.getUserFullName.length > 15
        ? `${this.getUserFullName.substring(0, 15)}...`
        : this.getUserFullName
    },
    hasSidebar() {
      return this.$route.matched.some(
        (record) => record.components != null && 'sidebar' in record.components
      )
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
    },

    login() {
      this.$router.push({ name: UserRouteName.Login })
    }
  }
})
</script>

<style lang="scss" scoped></style>
