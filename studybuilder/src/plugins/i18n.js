import { createI18n } from 'vue-i18n'
import en from '@/locales/en.json'

const instance = createI18n({
  legacy: false,
  locale: import.meta.env.VUE_APP_I18N_LOCALE || 'en',
  fallbackLocale: import.meta.env.VUE_APP_I18N_FALLBACK_LOCALE || 'en',
  messages: {
    en: en,
  },
})

export default instance
export const i18n = instance.global
