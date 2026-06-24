import { createI18n } from 'vue-i18n'

import EN from './translations/EN.js'

export type LocaleMessages = Record<string, string>
export type LocaleMessagesMap = Record<string, LocaleMessages>

export interface MerginI18nOptions {
  locale?: string
  messages?: LocaleMessagesMap
}

interface RuntimeI18nState {
  locale: string
  fallbackLocale: string
  messages: LocaleMessagesMap
}

export const DEFAULT_LOCALE = 'en'
const RUNTIME_I18N_STATE_KEY = '__MERGIN_RUNTIME_I18N__'

let merginI18n: ReturnType<typeof createI18n> | undefined

export const normalizeLocale = (locale?: string) =>
  locale?.trim().replace(/_/g, '-').toLowerCase() || undefined

const localMessages: LocaleMessagesMap = {
  [DEFAULT_LOCALE]: EN as LocaleMessages
}

export const getLocalTranslation = (key: string) =>
  localMessages[DEFAULT_LOCALE]?.[key]

const getRuntimeI18nState = () =>
  (
    globalThis as typeof globalThis &
      Record<typeof RUNTIME_I18N_STATE_KEY, RuntimeI18nState | undefined>
  )[RUNTIME_I18N_STATE_KEY]

const setRuntimeI18nState = (state: RuntimeI18nState) => {
  ;(
    globalThis as typeof globalThis &
      Record<typeof RUNTIME_I18N_STATE_KEY, RuntimeI18nState | undefined>
  )[RUNTIME_I18N_STATE_KEY] = state
}

export const getRuntimeTranslation = (key: string, locale?: string) => {
  const state = getRuntimeI18nState()

  if (!state) {
    return undefined
  }

  const normalizedLocale = normalizeLocale(locale) ?? state.locale

  return (
    state.messages[normalizedLocale]?.[key] ??
    state.messages[state.locale]?.[key] ??
    state.messages[state.fallbackLocale]?.[key]
  )
}

export const createMerginI18n = ({
  locale = DEFAULT_LOCALE,
  messages = {}
}: MerginI18nOptions = {}) => {
  const resolvedLocale = normalizeLocale(locale) ?? DEFAULT_LOCALE
  const resolvedMessages: LocaleMessagesMap = {
    [DEFAULT_LOCALE]: localMessages[DEFAULT_LOCALE]
  }

  Object.entries(messages).forEach(([messageLocale, localeMessages]) => {
    const normalizedLocale = normalizeLocale(messageLocale) ?? messageLocale
    resolvedMessages[normalizedLocale] = {
      ...(resolvedMessages[normalizedLocale] ?? {}),
      ...localeMessages
    }
  })

  const activeLocale = resolvedMessages[resolvedLocale]
    ? resolvedLocale
    : DEFAULT_LOCALE

  setRuntimeI18nState({
    locale: activeLocale,
    fallbackLocale: DEFAULT_LOCALE,
    messages: resolvedMessages
  })

  merginI18n = createI18n({
    legacy: false,
    locale: activeLocale,
    fallbackLocale: DEFAULT_LOCALE,
    messages: resolvedMessages,
    missingWarn: false,
    fallbackWarn: false
  })

  return merginI18n
}

export const getMerginI18n = () => merginI18n
