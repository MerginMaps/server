// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { ComponentCustomPropertyFilters } from '@mergin/lib'

import { MerginComponentUuid } from './modules/form/types'

declare module '*.vue' {
  import * as Vue from 'vue'
  export default Vue
}

// It seems that IntelliJ IDEs are using the @vue/runtime-core module for type checking in .vue <template> tags, instead of the augmented vue module.
// See: https://youtrack.jetbrains.com/issue/WEB-59818/Vue-custom-global-properties-added-by-augmenting-vue-are-not-resolved
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $filters: ComponentCustomPropertyFilters
    merginComponentUuid: MerginComponentUuid
  }
}
