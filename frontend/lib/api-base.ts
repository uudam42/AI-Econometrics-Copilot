let _cachedBaseUrl: string | null = null;

export async function getApiBaseUrl(): Promise<string> {
  if (_cachedBaseUrl) return _cachedBaseUrl;

  if (
    typeof window !== "undefined" &&
    "__TAURI_INTERNALS__" in window
  ) {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const url = await invoke<string>("get_backend_base_url");
      _cachedBaseUrl = url;
      return url;
    } catch {
      // Fall through to env-based URL
    }
  }

  _cachedBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  return _cachedBaseUrl;
}

export function getApiBaseUrlSync(): string {
  if (_cachedBaseUrl) return _cachedBaseUrl;
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
}

export function isDesktopMode(): boolean {
  return (
    typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
  );
}
