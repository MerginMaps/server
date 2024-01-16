// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export {}

/** There is missing toast in unplugin vue components, so added manually */
declare module 'vue' {
  export interface GlobalComponents {
    PToast: typeof import('primevue/toast')['default']
  }
}
