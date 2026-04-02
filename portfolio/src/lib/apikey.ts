export type LLMProviderId = "gemini" | "openai" | "anthropic" | "ollama";

export interface StoredLLMSelection {
  provider: LLMProviderId;
  model: string;
}

const activeApiKeys: Record<LLMProviderId, string> = {
  gemini: "",
  openai: "",
  anthropic: "",
  ollama: "",
};

let activeSelection: StoredLLMSelection | null = null;

export function getStoredApiKey(provider: LLMProviderId = "gemini"): string {
  return activeApiKeys[provider] ?? "";
}

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

export function clearStoredApiKey(provider: LLMProviderId = "gemini"): void {
  activeApiKeys[provider] = "";
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

export function clearStoredLLMSelection(): void {
  activeSelection = null;
}
