let activeApiKey = "";

export function getStoredApiKey(): string {
  return activeApiKey;
}

export function setStoredApiKey(key: string): void {
  activeApiKey = key.trim();
}

export function clearStoredApiKey(): void {
  activeApiKey = "";
}
