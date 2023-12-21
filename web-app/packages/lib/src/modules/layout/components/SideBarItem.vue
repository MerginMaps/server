<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<script lang="ts">
import { PropType, defineComponent } from 'vue'

import { SideBarItemModel } from '../types'

export default defineComponent({
  props: {
    item: Object as PropType<SideBarItemModel>
  }
})
</script>

<template>
  <li class="p-2">
    <router-link
      :class="[
        'sidebar-item__link px-3 py-2 flex align-items-center transition-color transition-duration-200 no-underline border-round-lg text-sm',
        item.active && 'sidebar-item__link--active'
      ]"
      :to="item.to"
      ><div class="mr-2"><i :class="['text-xl', item.icon]"></i></div>
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
