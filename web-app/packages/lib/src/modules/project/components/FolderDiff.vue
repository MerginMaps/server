<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template functional>
  <span class="diff">
    <span v-if="props.added" class="added">{{ props.added }}</span>
    <span v-if="props.removed" class="removed">{{ props.removed }}</span>
    <span v-if="props.updated" class="updated">{{ props.updated }}</span>
    <span v-if="props.added + props.removed + props.updated > 0">
      / {{ props.count }}</span
    >
  </span>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'FolderDiff',
  functional: true,
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
