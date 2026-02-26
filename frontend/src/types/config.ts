export interface Config {
  openai_api_key: string;
  soniox_api_key: string;
  target_lang: string;
}

export const LANGUAGES: Record<string, string> = {
  ko: '한국어',
  en: 'English',
  ja: '日本語',
  zh: '中文',
  vi: 'Tiếng Việt',
};
