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
  <li>
    <router-link
      :class="[
        'sidebar-item__link p-4 flex align-items-center transition-color transition-duration-200 no-underline',
        item.active && 'sidebar-item__link--active'
      ]"
      :to="item.to"
      ><div class="mr-2"><i :class="['text-2xl', item.icon]"></i></div>
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
      color: var(--surface-a);
      background-color: var(--forest-color);
      font-weight: 600;
    }
  }
}
</style>
