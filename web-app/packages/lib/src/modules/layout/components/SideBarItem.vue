<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<script setup lang="ts">
import { useLayoutStore } from '../store'
import { SideBarItemModel } from '../types'

defineProps<{ item: SideBarItemModel }>()
const layoutStore = useLayoutStore()

function closeDrawer() {
  layoutStore.isUnderOverlayBreakpoint &&
    layoutStore.setDrawer({ drawer: false })
}
</script>

<template>
  <li class="px-2">
    <router-link
      :class="[
        'sidebar-item__link p-3 flex align-items-center transition-color transition-duration-200 no-underline border-round-lg paragraph-p5',
        item.active && 'sidebar-item__link--active'
      ]"
      :to="item.to"
      @click.native="closeDrawer"
      ><div class="mr-2 flex align-items-center">
        <i :class="['paragraph-p3', item.icon]"></i>
      </div>
      <span>{{ item.title }}</span></router-link
    >
  </li>
</template>

<style lang="scss" scoped>
.sidebar-item {
  &__link {
    color: inherit;

    &:hover {
      color: var(--forest-color);
      background-color: var(--surface-a);
    }

    &--active {
      color: var(--forest-color);
      background-color: var(--light-green-color);
      font-weight: 600;
    }
  }
}
</style>
