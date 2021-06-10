# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
  <v-menu
    v-model="showMenu"
    :position-x="x"
    :position-y="y"
    absolute
    offset-y
    :min-width="150"
  >
    <v-list>
      <v-list-item @click="deleteFile">
        <v-list-item-title>Delete</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
export default {
  data () {
    return {
      showMenu: false,
      x: 0,
      y: 0,
      file: null
    }
  },
  methods: {
    open (evt, file) {
      this.showMenu = true
      this.x = evt.clientX
      this.y = evt.clientY
      this.file = file
    },
    deleteFile () {
      this.$store.commit('deleteFiles', [this.file.path])
    }
  }
}
</script>
