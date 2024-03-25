// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import uniqueId from 'lodash/uniqueId'

/**
 * Adds globally unique id to each instance of project component.
 */
export default {
  data() {
    return {
      merginComponentUuid: uniqueId()
    }
  }
}
