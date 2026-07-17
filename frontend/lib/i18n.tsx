"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { en } from "./translations/en";
import { zhCN } from "./translations/zh-CN";

export type { TranslationKey } from "./translations/en";
export type Language = "en" | "zh-CN";

const STORAGE_KEY = "ecopilot.language";

const dictionaries: Record<Language, Record<string, string>> = {
  en,
  "zh-CN": zhCN,
};

interface I18nContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue>({
  language: "en",
  setLanguage: () => {},
  t: (key) => (en as Record<string, string>)[key] ?? key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "en" || stored === "zh-CN") {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setLanguageState(stored);
      } else if (navigator.language.toLowerCase().startsWith("zh")) {
        setLanguageState("zh-CN");
      }
    } catch {
      // localStorage unavailable — keep default
    }
  }, []);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  }, []);

  const t = useCallback(
    (key: string) =>
      dictionaries[language][key] ?? (en as Record<string, string>)[key] ?? key,
    [language]
  );

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}
