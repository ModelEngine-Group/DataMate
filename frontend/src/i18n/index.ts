import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import zhCommon from './locales/zh/common.json';
import enCommon from './locales/en/common.json';

// Get saved language from localStorage, default to 'zh'
const savedLanguage = localStorage.getItem('language') || 'zh';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      zh: {
        common: zhCommon,
      },
      en: {
        common: enCommon,
      },
    },
    lng: savedLanguage,
    fallbackLng: 'zh',
    ns: ['common'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
