"use client";

import { useCallback, useEffect, useState } from "react";
import { isDesktopMode } from "@/lib/api-base";
import { DesktopStartupScreen } from "./DesktopStartupScreen";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [desktop, setDesktop] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const isDesktop = isDesktopMode();
    setDesktop(isDesktop);
    if (!isDesktop) {
      setReady(true);
    }
  }, []);

  const handleReady = useCallback(() => {
    setReady(true);
  }, []);

  if (desktop && !ready) {
    return <DesktopStartupScreen onReady={handleReady} />;
  }

  return <>{children}</>;
}
