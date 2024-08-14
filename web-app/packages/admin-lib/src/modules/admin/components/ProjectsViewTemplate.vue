<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <admin-layout>
    <v-layout class="column fill-height ml-10">
      <v-container>
        <v-row>
          <v-col>
            <v-layout align-center shrink>
              <h3 class="ml-1 my-2">
                <span v-if="namespace">
                  <v-icon class="arrow">chevron_right</v-icon>
                  {{ namespace }}</span
                >
              </h3>
              <v-spacer />
              <portal-target name="additional-action" />
            </v-layout>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-card class="table">
              <v-card-title> Projects</v-card-title>
              <v-card-text>
                <admin-projects-table
                  :key="namespace"
                  :show-namespace="showNamespace"
                  :namespace="namespace"
                  show-tags
                />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-layout>
  </admin-layout>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import AdminProjectsTable from '@/modules/admin/components/AdminProjectsTable.vue'

export default defineComponent({
  name: 'ProjectsView',
  components: {
    AdminProjectsTable,
    AdminLayout
  },
  props: {
    namespace: String,
    showNamespace: { type: Boolean, default: false }
  },
  data() {
    return {
      asAdmin: true
    }
  }
})
</script>

<style lang="scss" scoped>
h3 a {
  text-decoration: none;
}

.v-card.table {
  min-height: unset;
  overflow: unset;
}

.arrow {
  color: black;
  font-size: large;
}

@media (max-width: 400px) {
  .action-button {
    width: 135px;
  }
}

.action-button {
  div {
    display: inline-block;
  }
}
</style>
