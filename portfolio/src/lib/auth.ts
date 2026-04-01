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

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(AUTH_SESSION_KEY);
}