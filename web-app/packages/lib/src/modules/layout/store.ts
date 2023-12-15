// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore } from 'pinia'

export interface LayoutState {
  overlayBreakpoint: number
  drawer: boolean
  /** If sidebar is in overlay mode (on mobile is flying over content) */
  isOverlay: boolean
  /** Parsed closed elements from local storage and pushed back to local storage */
  closedElements: string[]
}

const CLOSED_ELEMENTS_KEY = 'mm-closed-elements'

export const useLayoutStore = defineStore('layoutModule', {
  state: (): LayoutState => ({
    overlayBreakpoint: 992,
    drawer: false,
    isOverlay: false,
    closedElements: []
  }),
  getters: {
    /**
     * Checks if an element ID is in the list of closed elements.
     *
     * @param state - The layout store state
     * @param elementId - The element ID to check
     * @returns True if the element ID is in the closed elements list
     */
    isClosedElement(state) {
      const { closedElements } = state
      return (elementId: string) => closedElements.includes(elementId)
    }
  },
  actions: {
    init() {
      this.updateScreenParams()
      window?.addEventListener('resize', this.updateScreenParams)

      this.getClosedElements()
    },
    updateScreenParams() {
      const width = window.innerWidth
      const isSmall =
        window.matchMedia !== undefined
          ? window.matchMedia(
              `screen and (max-width: ${this.overlayBreakpoint}px)`
            ).matches
          : width < this.overlayBreakpoint
      this.drawer = !isSmall
      this.isOverlay = isSmall
    },
    setDrawer(payload) {
      this.drawer = payload.drawer
    },
    getClosedElements() {
      const storageValue = window?.localStorage?.getItem(CLOSED_ELEMENTS_KEY)
      const parsed = JSON.parse(storageValue) ?? []
      this.closedElements = parsed
    },
    closeElement(elementId: string) {
      const storageValue = window?.localStorage?.getItem(CLOSED_ELEMENTS_KEY)
      const parsed = JSON.parse(storageValue) ?? []
      if (parsed.includes(elementId)) return

      parsed.push(elementId)
      window?.localStorage?.setItem(CLOSED_ELEMENTS_KEY, JSON.stringify(parsed))
      this.closedElements = parsed
    }
  }
})
