<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<script lang="ts">
import { SideBarItem, SideBarTemplate } from '@mergin/lib'
import { defineComponent, ref } from 'vue'
import { HomeIcon, MapIcon } from 'vue-tabler-icons'

export default defineComponent({
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

    return {
      mainItems
    }
  }
})
</script>


<template>
  <SideBarTemplate>
    <template #items>
      <v-list nav variant="flat" data-cy="side-bar-main-list">
        <template v-for="(item, i) in mainItems" :key="`item-${i}`">
          <side-bar-item :item="item" :id="`item-${i}`">
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
