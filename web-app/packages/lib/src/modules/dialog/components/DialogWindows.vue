<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-dialog :value="isDialogOpen" v-bind="dialogProps" @input="close">
    <div
      v-if="params"
      :is="params.component"
      v-bind="params.props"
      v-on="params.listeners"
    />
  </v-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { mapState, mapGetters, mapActions } from 'vuex'

export default defineComponent({
  computed: {
    ...mapState('dialogModule', ['isDialogOpen', 'params']),
    ...mapGetters('dialogModule', ['dialogProps'])
  },
  methods: {
    ...mapActions('dialogModule', ['close'])
  }
})
</script>
