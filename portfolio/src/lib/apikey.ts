export type LLMProviderId = "gemini" | "openai" | "anthropic" | "ollama";

export interface StoredLLMSelection {
  provider: LLMProviderId;
  model: string;
}

// ---------------------------------------------------------------------------
// API key storage.
//
// Keys are kept in an in-memory object only — never written to ``localStorage``,
// ``sessionStorage``, ``IndexedDB``, or cookies.  This limits blast radius if
// an XSS payload runs on the page: it can still read the current tab's keys
// but cannot persist or harvest them across reloads.
//
// ``clearStoredApiKeys()`` is called on logout, auth expiry, and provider
// switch to wipe state explicitly.  The portfolio UI should also wipe on
// ``visibilitychange`` when leaving the tab if that matters to your threat
// model.
// ---------------------------------------------------------------------------

const EMPTY_KEYS: Record<LLMProviderId, string> = {
  gemini: "",
  openai: "",
  anthropic: "",
  ollama: "",
};

const activeApiKeys: Record<LLMProviderId, string> = { ...EMPTY_KEYS };

let activeSelection: StoredLLMSelection | null = null;

export function getStoredApiKeys(): Record<LLMProviderId, string> {
  return { ...activeApiKeys };
}

export function setStoredApiKey(providerOrKey: LLMProviderId | string, key?: string): void {
  if (key === undefined) {
    activeApiKeys.gemini = String(providerOrKey).trim();
    return;
  }

  activeApiKeys[providerOrKey as LLMProviderId] = key.trim();
}

export function clearStoredApiKey(provider: LLMProviderId): void {
  activeApiKeys[provider] = "";
}

export function clearStoredApiKeys(): void {
  (Object.keys(activeApiKeys) as LLMProviderId[]).forEach((p) => {
    activeApiKeys[p] = "";
  });
  activeSelection = null;
}

export function getStoredLLMSelection(): StoredLLMSelection | null {
  return activeSelection ? { ...activeSelection } : null;
}

export function setStoredLLMSelection(selection: StoredLLMSelection): void {
  activeSelection = {
    provider: selection.provider,
    model: selection.model,
  };
}
