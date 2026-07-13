"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isDesktopMode } from "@/lib/api-base";
import { I18nProvider } from "@/lib/i18n";
import { DesktopStartupScreen } from "./DesktopStartupScreen";
import { AboutDialog } from "./desktop/AboutDialog";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [desktop, setDesktop] = useState(false);
  const [ready, setReady] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const isDesktop = isDesktopMode();
    setDesktop(isDesktop);
    if (!isDesktop) {
      setReady(true);
      return;
    }

    // Listen for menu actions emitted from Tauri
    let unlisten: (() => void) | null = null;
    import("@tauri-apps/api/event").then(({ listen }) => {
      listen<string>("menu_action", (event) => {
        const action = event.payload;
        if (action === "nav_home") {
          router.push("/");
        } else if (action === "nav_quick_analyze") {
          router.push("/quick-analyze");
        } else if (action === "nav_quick_start") {
          router.push("/quick-analyze");
        } else if (action === "show_about") {
          setAboutOpen(true);
        }
      }).then((fn) => {
        unlisten = fn;
      });
    }).catch(() => {});

    return () => {
      if (unlisten) unlisten();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleReady = useCallback(() => {
    setReady(true);
  }, []);

  if (desktop && !ready) {
    return <DesktopStartupScreen onReady={handleReady} />;
  }

  return (
    <I18nProvider>
      {children}
      {desktop && (
        <AboutDialog open={aboutOpen} onClose={() => setAboutOpen(false)} />
      )}
    </I18nProvider>
  );
}
