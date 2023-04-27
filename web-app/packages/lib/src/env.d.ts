// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VUE_APP_JOIN_COMMUNITY_LINK: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
