# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

<template>
   <page-view v-if="app.user.username === name"
      :style="`padding-left: ${drawer ? 260 : 20}px; overflow-y: auto; padding-right:20px; margin-right: 0px;`">
      <router-view></router-view>
  </page-view>
</template>

<script>
import PageView from '@/views/PageView'
import { mapState } from 'vuex'

export default {
  name: 'user-page',
  components: {
    PageView
  },
  computed: {
    ...mapState(['drawer', 'app']),
    name () {
      return this.$route.params.name
    }
  }
}
</script>

<style scoped>

.toggle-toolbar {
  position: fixed;
  left: 5px;
  z-index: 100;
  bottom: 20px;
}

</style>
