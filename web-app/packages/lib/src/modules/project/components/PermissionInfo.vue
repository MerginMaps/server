<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <a :href="docsLinkManagePermissions" target="_blank" class="info-link">
    <v-icon class="info-icon">info_outline</v-icon>
    <span class="text-caption font-weight-bold info-text ml-2"
      >Click here to learn more about roles and permissions</span
    >
  </a>
</template>

<script lang="ts">
import { mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useInstanceStore } from '@/modules/instance/store'

export default defineComponent({
  computed: {
    ...mapState(useInstanceStore, ['configData']),

    docsLinkManagePermissions(): string {
      return `${this.configData?.docs_url ?? ''}/manage/permissions`
    }
  }
})
</script>

<style lang="scss" scoped>
.info-link {
  text-decoration: none;
  margin-left: 0;
  margin-right: 0;
  padding-left: 0;
  padding-right: 0;
  display: flex;
  flex-direction: row;
  align-items: center;

  &:hover {
    opacity: 0.7;
  }
}

.info-icon {
  color: #121212;
}

.info-text {
  color: #121212;
  text-decoration: underline;
}
</style>
