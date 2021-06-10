<template>
  <page-view :style="`padding-left: ${drawer ? 260 : 20}px; overflow-y: auto; padding:right: 20px; margin-right: 0px`">
      <router-view></router-view>
  </page-view>
</template>

<script>
import PageView from '@/views/PageView'
import { mapMutations, mapState } from 'vuex'

export default {
  name: 'organisation-page',
  components: { PageView },
  computed: {
    ...mapState(['drawer', 'app']),
    name () {
      return this.$route.params.name
    }
  },
  methods: {
    ...mapMutations({
      setDrawer: 'SET_DRAWER'
    })
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
