// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Router from 'vue-router'

declare module '*.vue' {
  import * as Vue from 'vue'
  export default Vue
}

declare module 'pinia' {
  export interface Pinia {
    router: Router
  }
}
