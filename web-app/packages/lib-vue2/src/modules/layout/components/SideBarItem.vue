<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<script lang="ts">
import { defineComponent } from 'vue'

import BaseItem from '@/common/components/base/BaseItem.vue'

export default defineComponent({
  props: {
    item: Object,
    idx: Number
  },
  components: { BaseItem }
})
</script>

<template>
  <div>
    <base-item
      :id="`item-${idx}`"
      :key="`item-${idx}`"
      :item="item"
      color="primary"
      class="ma-0"
      data-cy="side-bar-main-items"
    >
      <template #icon>
        <slot name="icon"></slot>
      </template>
    </base-item>
  </div>
</template>

<style lang="scss" scoped>
.primary.v-list-item--active.v-list-item {
  background-color: #b0b1b5 !important;
}

.theme--dark.v-list-item:not(.v-list-item--active):not(.v-list-item--disabled) {
  color: #2d4470 !important;
}

.v-list-item--link:hover {
  background: rgba(0, 0, 0, 0.04) !important;
}

.theme--dark.v-card.v-list-item.v-list-item--link {
  min-height: 20px !important;
  padding: 5px 0 5px 0 !important;
}

::v-deep(.v-list-item) {
  font-size: 14px;
  color: #444;
  min-height: 32px;

  .v-list-item__content {
    padding: 0;
  }
}

a {
  text-decoration: none;
  margin-top: 5px;
}
</style>
