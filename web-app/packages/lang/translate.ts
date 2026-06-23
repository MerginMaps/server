import {
  getLocalTranslation,
  getMerginI18n,
  getRuntimeTranslation
} from './i18n'

const returnTranslation = (_lang: string, key: string) => {
  const i18n = getMerginI18n()

  if (i18n) {
    const translation = i18n.global.t(key)

    if (typeof translation === 'string' && translation !== key) {
      return translation
    }
  }

  const runtimeTranslation = getRuntimeTranslation(key, _lang)

  if (runtimeTranslation) {
    return runtimeTranslation
  }

  return getLocalTranslation(key) ?? key
}

export default returnTranslation
