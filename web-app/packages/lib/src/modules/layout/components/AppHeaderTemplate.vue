<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <PMenubar
    class="app-header pt-0 px-2"
    :pt="{
      start: {
        class: 'w-10'
      },
      end: {
        class: 'align-self-start lg:align-self-center'
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
            icon="ti ti-menu-2"
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
      <div>
        <slot name="invitationsIcon"></slot>
        <PButton
          text
          aria-haspopup="true"
          aria-controls="app-header-profile"
          class="text-color p-0"
          @click="toggleMenu"
        >
          <div class="mr-2">
            <p>{{ getUserFullName }}</p>
            <p v-if="renderNamespace" class="font-normal">
              {{ currentNamespace || 'no workspace' }}
            </p>
          </div>
          <i class="ti ti-chevron-down"></i
        ></PButton>
        <POverlayPanel
          id="app-header-profile"
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
                  class: 'surface-ground mr-2 text-color-forest font-semibold',
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
      </div>
    </template>
  </PMenubar>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { MenuItem } from 'primevue/menuitem'
import { defineComponent, ref, PropType } from 'vue'

import { AppBreadcrumbs } from '.'

import { useLayoutStore } from '@/modules/layout/store'
import { useProjectStore } from '@/modules/project/store'
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
    ...mapState(useLayoutStore, ['drawer']),
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
    avatarLabel() {
      return this.getUserFullName.charAt(0).toUpperCase()
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
