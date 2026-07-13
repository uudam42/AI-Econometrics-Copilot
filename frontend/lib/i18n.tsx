"use client";

/**
 * Lightweight client-side i18n.
 *
 * Next.js built-in i18n routing is unavailable with `output: "export"`
 * (required for the Tauri desktop build), so language is a client concern:
 * a React context + dictionary lookup, persisted to localStorage.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

export type Language = "en" | "zh-CN";

const STORAGE_KEY = "ecopilot.language";

// ---------------------------------------------------------------------------
// Dictionaries
// ---------------------------------------------------------------------------

const en = {
  // Common
  "app.title": "AI Econometrics Copilot",
  "app.tagline": "Explainable, reproducible econometric analysis",
  "common.back_home": "← Home",
  "common.loading": "Loading…",
  "common.error": "Something went wrong.",
  "common.empty": "Nothing here yet.",
  "common.open": "Open",
  "common.rows": "rows",
  "common.columns": "columns",
  "common.created": "Created",
  "common.uploaded": "Uploaded",
  "common.project": "Project",
  "common.no_project": "No project",

  // Home
  "home.my_projects": "My Projects",
  "home.hero": "What would you like to do?",
  "home.hero_sub":
    "Choose a path below — you can always switch to the full Research Workspace later.",
  "home.card_quick_title": "Analyse My Excel / CSV",
  "home.card_quick_desc":
    "Upload your file, answer one question, and get a plain-language result in under a minute.",
  "home.card_demo_title": "Try a Demo Dataset",
  "home.card_demo_desc":
    "Load a sample World Bank panel dataset and explore the full workflow.",
  "home.card_demo_unavailable": "Demo data not available on this installation.",
  "home.card_projects_title": "Open Previous Project",
  "home.card_projects_desc":
    "Return to a project you have already started and continue your research.",
  "home.creating_demo": "Creating demo project…",
  "home.demo_error": "Could not create demo project.",
  "home.advanced": "Advanced workflow",
  "home.link_datasets": "📂 All Datasets",
  "home.link_projects": "🗂 All Projects",
  "home.link_reports": "📄 Reports",
  "home.link_analyses": "🔬 Analyses",
  "home.footer":
    "Statistical associations only — not causal effects unless additional identification assumptions are justified.",

  // Datasets index
  "datasets.title": "All Datasets",
  "datasets.subtitle": "Every dataset uploaded to this workspace.",
  "datasets.empty":
    "No datasets uploaded yet. Use Quick Analyze or a project to upload one.",
  "datasets.model": "Model",
  "datasets.plan": "Plan",

  // Analyses index
  "analyses.title": "All Analyses",
  "analyses.subtitle": "Every analysis run in this workspace.",
  "analyses.empty": "No analyses run yet.",
  "analyses.model_type": "Model",
  "analyses.dependent": "Dependent variable",

  // Reports index
  "reports.title": "All Reports",
  "reports.subtitle": "Every research report generated in this workspace.",
  "reports.empty": "No reports generated yet.",
  "reports.source": "Source",

  // Language switcher
  "lang.switch_to": "中文",
} as const;

export type TranslationKey = keyof typeof en;

const zhCN: Record<TranslationKey, string> = {
  // Common
  "app.title": "AI 计量经济学助手",
  "app.tagline": "可解释、可复现的计量经济分析",
  "common.back_home": "← 首页",
  "common.loading": "加载中…",
  "common.error": "出错了。",
  "common.empty": "暂无内容。",
  "common.open": "打开",
  "common.rows": "行",
  "common.columns": "列",
  "common.created": "创建于",
  "common.uploaded": "上传于",
  "common.project": "项目",
  "common.no_project": "无所属项目",

  // Home
  "home.my_projects": "我的项目",
  "home.hero": "您想做什么？",
  "home.hero_sub": "选择下方任一入口 — 随时可以切换到完整的研究工作区。",
  "home.card_quick_title": "分析我的 Excel / CSV",
  "home.card_quick_desc": "上传文件，回答一个问题，一分钟内获得通俗易懂的分析结果。",
  "home.card_demo_title": "试用演示数据集",
  "home.card_demo_desc": "加载世界银行面板样本数据集，体验完整工作流程。",
  "home.card_demo_unavailable": "当前安装不包含演示数据。",
  "home.card_projects_title": "打开已有项目",
  "home.card_projects_desc": "回到您已开始的项目，继续您的研究。",
  "home.creating_demo": "正在创建演示项目…",
  "home.demo_error": "无法创建演示项目。",
  "home.advanced": "高级工作流",
  "home.link_datasets": "📂 全部数据集",
  "home.link_projects": "🗂 全部项目",
  "home.link_reports": "📄 研究报告",
  "home.link_analyses": "🔬 分析记录",
  "home.footer": "本工具仅识别统计关联性 — 除非额外的识别假设已被证明合理，否则不构成因果结论。",

  // Datasets index
  "datasets.title": "全部数据集",
  "datasets.subtitle": "此工作区中上传的所有数据集。",
  "datasets.empty": "还没有上传数据集。可通过快速分析或项目上传。",
  "datasets.model": "建模",
  "datasets.plan": "规划",

  // Analyses index
  "analyses.title": "全部分析",
  "analyses.subtitle": "此工作区中运行过的所有分析。",
  "analyses.empty": "还没有运行过分析。",
  "analyses.model_type": "模型",
  "analyses.dependent": "因变量",

  // Reports index
  "reports.title": "全部报告",
  "reports.subtitle": "此工作区中生成的所有研究报告。",
  "reports.empty": "还没有生成报告。",
  "reports.source": "来源",

  // Language switcher
  "lang.switch_to": "English",
};

const dictionaries: Record<Language, Record<TranslationKey, string>> = {
  en,
  "zh-CN": zhCN,
};

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface I18nContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextValue>({
  language: "en",
  setLanguage: () => {},
  t: (key) => en[key],
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  // Language must be applied after hydration: the static export always
  // renders English, and reading localStorage during render would cause a
  // server/client hydration mismatch.
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
    (key: TranslationKey) => dictionaries[language][key] ?? en[key],
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
