// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'
import { Module } from 'vuex'

import { RootState } from '@/modules/types'

export interface LayoutState {
  barColor: string
  barImage: string
  drawer: boolean
}

export const useLayoutStore = defineStore('layoutModule', {
  state: (): LayoutState => ({
    barColor: 'rgba(176, 177, 181 1), rgba(176, 177, 181 1)', // TODO: global - check if necessary and useful, MV-2022-06-30: I would probably get rid of this if possible
    barImage:
      'https://demos.creative-tim.com/material-dashboard/assets/img/sidebar-1.jpg', // TODO: global - check if necessary and useful, MV-2022-06-30: I would probably get rid of this if possible
    drawer: null
  }),

  actions: {
    setBarImage(payload) {
      this.barImage = payload.barImage
    },
    setDrawer(payload) {
      this.drawer = payload.drawer
    }
  }
})

const LayoutStore: Module<LayoutState, RootState> = {
  namespaced: true,
  state: {
    barColor: 'rgba(176, 177, 181 1), rgba(176, 177, 181 1)', // TODO: global - check if necessary and useful, MV-2022-06-30: I would probably get rid of this if possible
    barImage:
      'https://demos.creative-tim.com/material-dashboard/assets/img/sidebar-1.jpg', // TODO: global - check if necessary and useful, MV-2022-06-30: I would probably get rid of this if possible
    drawer: null
  },

  mutations: {
    setBarImage(state, payload) {
      state.barImage = payload.barImage
    },
    setDrawer(state, payload) {
      state.drawer = payload.drawer
    }
  }
}

export default LayoutStore
