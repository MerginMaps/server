export type StorageValue<T = object> = T extends object
  ? T
  : { [key: string]: T }

export type StorageProxy<T> = {
  value?: StorageValue<T>
}

export function createStorage<T>(
  storageKey: string,
  defaultValue: StorageValue<T>
) {
  return new Proxy<StorageProxy<T>>(
    { value: defaultValue },
    {
      get(target, propKey): StorageValue<T> {
        if (propKey !== 'value') {
          return undefined
        }

        const item = localStorage.getItem(storageKey)
        const result = item
          ? (JSON.parse(item)[propKey] as StorageValue<T>)
          : defaultValue

        target[propKey] = result
        return result
      },
      set(target, propKey: string, value: StorageValue<T>) {
        target.value = value
        localStorage.setItem(storageKey, JSON.stringify(target))
        return true
      },
      deleteProperty() {
        localStorage.removeItem(storageKey)
        return true
      }
    }
  )
}
