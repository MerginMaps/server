// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'

export interface LayoutState {
  sidebarBreakpoint: number
  drawer: boolean
  /** If sidebar is in overlay mode (on mobile is flying over content) */
  isOverlay: boolean
}

export const useLayoutStore = defineStore('layoutModule', {
  state: (): LayoutState => ({
    sidebarBreakpoint: 992,
    drawer: false,
    isOverlay: false
  }),

  actions: {
    init() {
      this.updateScreenParams()
      window?.addEventListener('resize', this.updateScreenParams)
    },
    updateScreenParams() {
      const width = window.innerWidth
      const isSmall =
        window.matchMedia !== undefined
          ? window.matchMedia(
              `screen and (max-width: ${this.sidebarBreakpoint}px)`
            ).matches
          : width < this.sidebarBreakpoint
      this.drawer = !isSmall
      this.isOverlay = isSmall
    },
    setDrawer(payload) {
      this.drawer = payload.drawer
    }
  }
})
