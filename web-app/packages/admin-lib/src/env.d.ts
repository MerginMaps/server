// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/// <reference types="vite/client" />

interface ImportMetaEnv {
  VITE_VUE_APP_I18N_LOCALE: string
  VITE_VUE_APP_I18N_FALLBACK_LOCALE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
