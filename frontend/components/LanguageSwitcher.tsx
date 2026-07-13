"use client";

import { useI18n } from "@/lib/i18n";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  return (
    <button
      type="button"
      onClick={() => setLanguage(language === "en" ? "zh-CN" : "en")}
      className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-accent/50 hover:text-accent"
      aria-label="Switch language"
      title={language === "en" ? "切换到中文" : "Switch to English"}
    >
      🌐 {t("lang.switch_to")}
    </button>
  );
}
