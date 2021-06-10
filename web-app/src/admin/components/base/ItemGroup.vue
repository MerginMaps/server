<template>
  <v-list-group
    :group="group"
    :sub-group="subGroup"
    :color="barColor !== 'rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.7)' ? 'white' : 'grey darken-1'"
    disabled
    :value="true">
    <template v-slot:activator>
      <v-list-item-icon
        v-if="text"
        class="v-list-item__icon--text"
        v-text="computedText"
        :class="`${color}--text`"
      />
      <v-list-item-icon v-else-if="item.icon">
      <v-icon
        :class="`${color}--text`"
        v-text="item.icon"
      />
    </v-list-item-icon>
      <v-list-item-avatar
        v-else-if="item.avatar"
        class="align-self-center"
        color="white"
        :class="`${color}--text`"
        contain
      >
        <v-img src="https://demos.creative-tim.com/vuetify-material-dashboard/favicon.ico" />
      </v-list-item-avatar>

      <v-list-item-content>
        <v-list-item-title v-text="item.title" :class="`${color}--text`"/>
      </v-list-item-content>
    </template>

    <template v-for="(child, i) in children">
      <base-item-sub-group
        v-if="child.children"
        :key="`sub-group-${i}`"
        :item="child"
      />

      <base-item
        v-else
        :key="`item-${i}`"
        :item="child"
        :color="color"
      />
    </template>
  </v-list-group>
</template>

<script>
// Utilities
import kebabCase from 'lodash/kebabCase'
import { mapState } from 'vuex'

export default {
  name: 'ItemGroup',

  inheritAttrs: false,

  props: {
    item: {
      type: Object,
      default: () => ({
        avatar: undefined,
        group: undefined,
        title: undefined,
        children: []
      })
    },
    subGroup: {
      type: Boolean,
      default: false
    },
    text: {
      type: Boolean,
      default: false
    },
    color: {
      type: String,
      default: 'white'
    }
  },

  computed: {
    ...mapState(['barColor']),
    children () {
      return this.item.children.map(item => ({
        ...item,
        to: !item.to ? undefined : `${this.item.group}/${item.to}`
      }))
    },
    computedText () {
      if (!this.item || !this.item.title) return ''

      let text = ''

      this.item.title.split(' ').forEach(val => {
        text += val.substring(0, 1)
      })

      return text
    },
    group () {
      return this.genGroup(this.item.children)
    }
  },

  methods: {
    genGroup (children) {
      return children
        .filter(item => item.to)
        .map(item => {
          const parent = item.group || this.item.group
          let group = `${parent}/${kebabCase(item.to)}`

          if (item.children) {
            group = `${group}|${this.genGroup(item.children)}`
          }

          return group
        }).join('|')
    }
  }
}
</script>

<style>
.v-list-group__activator p {
  margin-bottom: 0;
}
</style>
