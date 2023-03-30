<!--
Based on template:
Product Page: https://www.creative-tim.com/product/vuetify-material-dashboard
Copyright 2019 Creative Tim (https://www.creative-tim.com)

Modifications by:
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <v-list-item
    :href="href"
    :rel="href && href !== '#' ? 'noopener' : undefined"
    :target="href && href !== '#' ? '_blank' : undefined"
    :to="item.to"
    active-class="baseItemActiveColor"
  >
    <v-list-item-icon
      v-if="text"
      class="v-list-item__icon--text"
      v-text="computedText"
      :class="`${color}--text`"
    />

    <v-list-item-icon
      v-else-if="item.icon || item.tablerIcon"
      class="mr-2"
      :class="`${color}--text`"
    >
      <v-icon v-if="item.icon" :class="`${color}--text`" v-text="item.icon" />
      <slot v-if="item.tablerIcon" name="icon"></slot>
    </v-list-item-icon>

    <v-list-item-content
      v-if="item.title || item.subtitle"
      :class="`${color}--text`"
    >
      <v-list-item-title v-text="item.title" />

      <v-list-item-subtitle v-text="item.subtitle" />
    </v-list-item-content>
  </v-list-item>
</template>

<script lang="ts">
import Vue from 'vue'
import Themeable from 'vuetify/lib/mixins/themeable'

export default Vue.extend({
  name: 'Item',

  mixins: [Themeable],

  props: {
    color: {
      type: String,
      default: 'white'
    },
    item: {
      type: Object,
      default: () => ({
        href: undefined,
        icon: undefined,
        tablerIcon: false,
        subtitle: undefined,
        title: undefined,
        to: undefined
      })
    },
    text: {
      type: Boolean,
      default: false
    }
  },

  computed: {
    computedText() {
      if (!this.item || !this.item.title) return ''

      let text = ''

      this.item.title.split(' ').forEach((val) => {
        text += val.substring(0, 1)
      })

      return text
    },
    href() {
      return this.item.href || (this.item.to ? undefined : '#')
    }
  }
})
</script>

<style lang="scss" scoped>
.baseItemActiveColor {
  background-color: #f3f4f8;
}
</style>
