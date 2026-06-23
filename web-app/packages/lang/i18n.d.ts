export type LocaleMessages = Record<string, string>;
export type LocaleMessagesMap = Record<string, LocaleMessages>;
export interface MerginI18nOptions {
    locale?: string;
    messages?: LocaleMessagesMap;
}
export declare const DEFAULT_LOCALE = "en";
export declare const normalizeLocale: (locale?: string) => string;
export declare const getLocalTranslation: (key: string) => string;
export declare const getRuntimeTranslation: (key: string, locale?: string) => string;
export declare const createMerginI18n: ({ locale, messages }?: MerginI18nOptions) => import("vue-i18n").I18n<Record<string, unknown>, Record<string, unknown>, Record<string, unknown>, unknown, boolean>;
export declare const getMerginI18n: () => import("vue-i18n").I18n<Record<string, unknown>, Record<string, unknown>, Record<string, unknown>, unknown, boolean>;
