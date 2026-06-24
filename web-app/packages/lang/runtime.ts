import {
  createMerginI18n,
  DEFAULT_LOCALE,
  normalizeLocale,
  type LocaleMessages
} from './i18n'

interface WeblateConfig {
  baseUrl: string
  project: string
  component: string
}

interface ConfiguredLocale {
  normalizedLocale: string
}

const DEFAULT_WEBLATE_TIMEOUT_MS = 1000

const isMessagesMap = (value: unknown): value is LocaleMessages =>
  typeof value === 'object' &&
  value !== null &&
  !Array.isArray(value) &&
  Object.values(value).every((message) => typeof message === 'string')

const getEnvString = (value: unknown) =>
  typeof value === 'string' ? value.trim() : ''

const getConfiguredLocale = (): ConfiguredLocale => {
  const rawLocale = getEnvString(import.meta.env.VITE_LANG)

  return {
    normalizedLocale: normalizeLocale(rawLocale) ?? DEFAULT_LOCALE
  }
}

const getWeblateTimeoutMs = () => {
  const timeoutMs = Number(
    getEnvString(import.meta.env.VITE_WEBLATE_TIMEOUT_MS)
  )

  return Number.isFinite(timeoutMs) && timeoutMs > 0
    ? timeoutMs
    : DEFAULT_WEBLATE_TIMEOUT_MS
}

const getWeblateBaseUrl = (configuredBaseUrl: string) => {
  const baseUrl = configuredBaseUrl.replace(/\/+$/, '')

  if (!baseUrl || baseUrl.startsWith('/') || /^https?:\/\//i.test(baseUrl)) {
    return baseUrl
  }

  return `https://${baseUrl}`
}

const getWeblateConfig = (): WeblateConfig | undefined => {
  const configuredBaseUrl = getEnvString(import.meta.env.VITE_WEBLATE_URL)
  const baseUrl = getWeblateBaseUrl(configuredBaseUrl)
  const project = getEnvString(import.meta.env.VITE_WEBLATE_PROJECT)
  const component = getEnvString(import.meta.env.VITE_WEBLATE_COMPONENT)

  if (!baseUrl || !project || !component) {
    return undefined
  }

  return { baseUrl, project, component }
}

const buildWeblateFileUrl = (
  { baseUrl, project, component }: WeblateConfig,
  locale: string
) =>
  `${baseUrl}/api/translations/${encodeURIComponent(
    project
  )}/${encodeURIComponent(component)}/${encodeURIComponent(locale)}/file/`

const fetchMessages = async (
  locale: string,
  config: WeblateConfig | undefined
) => {
  if (!config) {
    return undefined
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), getWeblateTimeoutMs())

  try {
    const response = await fetch(buildWeblateFileUrl(config, locale), {
      signal: controller.signal
    })

    if (!response.ok) {
      return undefined
    }

    const messages = await response.json()

    if (!isMessagesMap(messages)) {
      return undefined
    }

    return messages
  } catch {
    return undefined
  } finally {
    clearTimeout(timeoutId)
  }
}

export const initializeRuntimeI18n = async () => {
  const config = getWeblateConfig()
  const { normalizedLocale } = getConfiguredLocale()
  const requestedMessages = await fetchMessages(normalizedLocale, config)

  return createMerginI18n({
    locale: normalizedLocale,
    messages: requestedMessages ? { [normalizedLocale]: requestedMessages } : {}
  })
}
