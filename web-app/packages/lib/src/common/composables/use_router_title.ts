// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { computed, toValue } from 'vue'
import { useRoute } from 'vue-router'

interface RouterTitleConfig {
  defaultTitle?: string | string[]
}

const SEPARATOR = ' \u2022 ' // Unicode for bullet character

const useRouterTitle = (config: RouterTitleConfig = {}, extended = {}) => {
  const route = useRoute()

  const metaTitle = computed<string | string[]>(() => {
    const metaTitle = route.meta.title
    const defaultTitle = config.defaultTitle
    if (!metaTitle) {
      return defaultTitle
    }
    if (typeof metaTitle === 'function') {
      return metaTitle(route, toValue(extended)) || defaultTitle
    }
    return metaTitle
  })

  const title = computed<string>(() => {
    const result = metaTitle.value
    if (Array.isArray(result)) {
      return result.filter(Boolean).join(` ${SEPARATOR} `)
    }
    return result
  })

  return {
    metaTitle,
    title
  }
}

export default useRouterTitle
