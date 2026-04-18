import { clearStoredApiKeys } from "@/lib/apikey";

const AUTH_SESSION_KEY = "portfolio.authenticated";
export const AUTH_SESSION_MARKER = "cookie-session";

export function getStoredAuthSession(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.sessionStorage.getItem(AUTH_SESSION_KEY) === "1"
    ? AUTH_SESSION_MARKER
    : null;
}

export function storeAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(AUTH_SESSION_KEY, "1");
}

/**
 * Clear the frontend auth marker AND wipe any in-memory LLM provider API
 * keys.  Previously ``apikey.ts`` kept keys in module-level mutable globals
 * that outlived logout and were accessible to any XSS payload running on
 * subsequent pages (C-9 in the audit).
 */
export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(AUTH_SESSION_KEY);
  clearStoredApiKeys();
}
