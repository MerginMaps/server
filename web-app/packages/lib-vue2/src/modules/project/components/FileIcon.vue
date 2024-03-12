<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <div>
    <template v-if="icon">
      <span>
        <img :src="icon" />
      </span>
    </template>
    <template v-else>
      <v-icon>{{ mdi }}</v-icon>
    </template>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

import mIconDbSchema from '@/assets/qgis-icons/mIconDbSchema.svg'
import mIconFolder from '@/assets/qgis-icons/mIconFolder.svg'
import mIconRaster from '@/assets/qgis-icons/mIconRaster.svg'
import mIconTableLayer from '@/assets/qgis-icons/mIconTableLayer.svg'
import mIconZip from '@/assets/qgis-icons/mIconZip.svg'
import providerQgis from '@/assets/qgis-icons/providerQgis.svg'

const mdiByExtensionDict = {
  jpg: 'image',
  jpeg: 'image',
  png: 'image'
}

const iconByExtensionDict = {
  folder: mIconFolder,
  gpkg: mIconDbSchema,
  qgs: providerQgis,
  qgz: providerQgis,
  rar: mIconZip,
  sql: mIconDbSchema,
  tif: mIconRaster,
  tiff: mIconRaster,
  xls: mIconTableLayer,
  xlsx: mIconTableLayer
}

export default defineComponent({
  props: {
    file: Object
  },
  computed: {
    icon: function () {
      const file = this.file
      const splittedName = file.name.split('.')
      let ext = splittedName[splittedName.length - 1].toLowerCase()
      if (file.type === 'folder') {
        if (file.name !== '..') {
          ext = 'folder'
        } else {
          return null
        }
      }
      return iconByExtensionDict[ext] ? iconByExtensionDict[ext] : null
    },
    mdi: function () {
      const file = this.file
      let mdi
      if (file.type === 'folder') {
        if (file.name !== '..') {
          mdi = 'folder'
        }
      } else {
        const splittedName = file.name.split('.')
        const ext = splittedName[splittedName.length - 1].toLowerCase()
        mdi = mdiByExtensionDict[ext] ? mdiByExtensionDict[ext] : 'description'
      }
      return mdi
    }
  }
})
</script>
<style lang="scss" scoped>
div {
  display: inline-block;
}

span {
  position: relative;
  display: inline-block;
  margin-right: 5px;
  height: 18px;
  width: 23px;
}

img {
  height: 100%;
  position: absolute;
  top: 3px;
  left: 2px;
}
</style>
