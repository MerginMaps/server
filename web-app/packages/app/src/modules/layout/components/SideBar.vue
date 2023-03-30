<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<script lang="ts">
import { SideBarItem, SideBarTemplate } from '@mergin/lib'
import { ref } from '@vue/composition-api'
import Vue from 'vue'
import { HomeIcon, MapIcon } from 'vue-tabler-icons'
import { useState } from 'vuex-composition-helpers'

export default Vue.extend({
  props: {
    expandOnHover: {
      type: Boolean,
      default: false
    }
  },
  components: { HomeIcon, MapIcon, SideBarTemplate, SideBarItem },
  setup() {
    const mainItems = ref([
      {
        title: 'Home',
        to: '/dashboard',
        tablerIcon: 'home-icon'
      },
      {
        title: 'Projects',
        to: '/projects',
        tablerIcon: 'map-icon'
      }
    ])
    const { loggedUser } = useState('userModule', ['loggedUser'])
    return {
      loggedUser,
      mainItems
    }
  }
})
</script>

<template>
  <SideBarTemplate>
    <template #items>
      <v-list nav flat data-cy="side-bar-main-list">
        <template v-for="(item, i) in mainItems">
          <side-bar-item :item="item" :id="`item-${i}`" :key="`item-${i}`">
            <template #icon>
              <component :is="item.tablerIcon"></component>
            </template>
          </side-bar-item>
        </template>
      </v-list>
    </template>
  </SideBarTemplate>
</template>

<style lang="scss" scoped></style>
