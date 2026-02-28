import { createContext, useContext, type ReactNode } from 'react';
import { getT, type Msgs } from './i18n';

type TFn = (key: keyof Msgs, arg?: string | number) => string;

const LocaleContext = createContext<TFn>(getT('ko'));

export function LocaleProvider({ lang, children }: { lang: string; children: ReactNode }) {
  return (
    <LocaleContext.Provider value={getT(lang)}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useT() {
  return useContext(LocaleContext);
}
