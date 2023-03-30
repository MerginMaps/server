// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

export function waitCursor(on: boolean) {
  document.body.style.cursor = on ? 'wait' : 'default'
}

export function downloadJsonList(jsonList, headers, filename, output = 'csv') {
  /** download json as csv, but we need to put it in one level
   :param jsonList: dict **/
  if (!jsonList || !headers) {
    return
  }
  headers = headers.filter((h) => h.value)
  const headerTexts = Object.keys(headers).map(function (key) {
    return headers[key].text
  })
  const headerValues = Object.keys(headers).map(function (key) {
    return headers[key].value
  })
  if (output === 'csv') {
    let content = headerTexts.join(';') + '\n'
    jsonList.forEach(function (row) {
      let currentContent = ''
      headerValues.forEach(function (header) {
        const headerSplit = header.split('.')
        if (headerSplit.length > 1) {
          currentContent +=
            (row[headerSplit[0]][headerSplit[1]] !== null
              ? row[headerSplit[0]][headerSplit[1]]
              : '') + ';'
        } else {
          currentContent += (row[header] !== null ? row[header] : '') + ';'
        }
      })
      content += currentContent + '\n'
    })
    const hiddenElement = document.createElement('a')
    hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(content)
    hiddenElement.target = '_blank'
    hiddenElement.download = filename + '.csv'
    hiddenElement.click()
    document.removeChild(hiddenElement)
  }
}
