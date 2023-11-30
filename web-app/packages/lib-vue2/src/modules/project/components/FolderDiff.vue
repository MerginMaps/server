<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <span class="diff">
    <span v-if="added" class="added">{{ added }}</span>
    <span v-if="removed" class="removed">{{ removed }}</span>
    <span v-if="updated" class="updated">{{ updated }}</span>
    <span v-if="added + removed + updated > 0"> / {{ count }}</span>
  </span>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'FolderDiff',
  props: {
    added: Number,
    removed: Number,
    updated: Number,
    count: Number
  }
})
</script>
<style lang="scss" scoped>
.added {
  color: green;
}

.removed {
  color: red;
}

.updated {
  color: orange;
}

.diff {
  // color: #777;
}

.diff > span {
  &:not(:first-child):not(:last-child) {
    &:before {
      content: ' + ';
      color: #777;
    }
  }
}
</style>
